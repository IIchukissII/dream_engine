"""Storm-Logos API: FastAPI backend for therapy and dream analysis.

Run with:
    uvicorn storm_logos.services.api.main:app --reload --port 8000

Or in Docker:
    docker-compose up api
"""

import os
import sys
import time
from pathlib import Path
from contextlib import asynccontextmanager
from collections import defaultdict
from typing import Optional

from fastapi import FastAPI, Request, HTTPException, status, Depends
from fastapi.middleware.cors import CORSMiddleware

# Ensure storm_logos is importable
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from .deps import load_env, get_user_graph, get_dream_engine, get_semantic_data, get_superuser, get_current_user, get_optional_user
from .routers import auth_router, sessions_router, evolution_router

# Load environment
load_env()


# =============================================================================
# RATE LIMITING
# =============================================================================
class RateLimiter:
    """Simple in-memory rate limiter."""

    def __init__(self, requests_per_minute: int = 60):
        self.requests_per_minute = requests_per_minute
        self.requests = defaultdict(list)

    def is_allowed(self, client_ip: str) -> bool:
        """Check if request is allowed for this client."""
        now = time.time()
        minute_ago = now - 60

        # Clean old requests
        self.requests[client_ip] = [
            req_time for req_time in self.requests[client_ip]
            if req_time > minute_ago
        ]

        # Check limit
        if len(self.requests[client_ip]) >= self.requests_per_minute:
            return False

        # Record request
        self.requests[client_ip].append(now)
        return True


# Initialize rate limiter (60 requests/min default, 120 for authenticated)
rate_limiter = RateLimiter(requests_per_minute=60)


def get_cors_origins() -> list:
    """Get CORS origins from environment variable."""
    origins_str = os.environ.get("CORS_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000")
    origins = [origin.strip() for origin in origins_str.split(",") if origin.strip()]
    return origins


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize services on startup."""
    print("Starting Storm-Logos API...")

    # Initialize services
    print("  Loading semantic data...")
    data = get_semantic_data()
    print(f"    {data.n_coordinates:,} coordinates")

    print("  Connecting to Neo4j...")
    ug = get_user_graph()
    if ug._connected:
        print("    Connected")
    else:
        print("    Warning: Neo4j not connected")

    print("  Initializing DreamEngine...")
    engine = get_dream_engine()
    print(f"    Model: {engine.model}")

    print("Storm-Logos API ready!")

    yield

    # Cleanup
    print("Shutting down...")


app = FastAPI(
    title="Storm-Logos API",
    description="""
Therapy and Dream Analysis API powered by semantic coordinates and Jungian archetypes.

## Features

- **Authentication**: Register and login to track your evolution
- **Sessions**: Start therapy or dream exploration sessions
- **Evolution**: Track how your archetypes manifest over time

## Archetypes

- shadow: The repressed, unknown aspects of self
- anima_animus: The contrasexual aspect of the psyche
- self: Wholeness and integration
- mother: Nurturing/devouring maternal principle
- father: Authority, order, spiritual principle
- hero: The ego's journey toward individuation
- trickster: Agent of change, boundary-crossing
- death_rebirth: Transformation through symbolic death
""",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS middleware - origins from environment
app.add_middleware(
    CORSMiddleware,
    allow_origins=get_cors_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# =============================================================================
# RATE LIMITING MIDDLEWARE
# =============================================================================
@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    """Apply rate limiting to all requests."""
    # Get client IP (handle proxies)
    client_ip = request.headers.get("X-Forwarded-For", request.client.host)
    if client_ip and "," in client_ip:
        client_ip = client_ip.split(",")[0].strip()

    # Skip rate limiting for health checks
    if request.url.path in ["/health", "/"]:
        return await call_next(request)

    # Check rate limit
    if not rate_limiter.is_allowed(client_ip):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded. Please try again later.",
            headers={"Retry-After": "60"}
        )

    response = await call_next(request)
    return response

# Include routers
app.include_router(auth_router)
app.include_router(sessions_router)
app.include_router(evolution_router)


@app.get("/")
async def root():
    """API root - health check."""
    return {
        "service": "storm-logos",
        "status": "running",
        "docs": "/docs",
    }


@app.get("/health")
async def health():
    """Basic health check endpoint."""
    return {"status": "healthy"}


@app.get("/health/ready")
async def health_ready():
    """Readiness check - verifies all dependencies are available."""
    checks = {
        "api": "healthy",
        "postgres": "unknown",
        "neo4j": "unknown",
    }
    all_healthy = True

    # Check PostgreSQL
    try:
        data = get_semantic_data()
        if data and data.n_coordinates > 0:
            checks["postgres"] = "healthy"
        else:
            checks["postgres"] = "degraded"
            all_healthy = False
    except Exception as e:
        checks["postgres"] = f"unhealthy: {str(e)[:50]}"
        all_healthy = False

    # Check Neo4j
    try:
        ug = get_user_graph()
        if ug._connected:
            checks["neo4j"] = "healthy"
        else:
            checks["neo4j"] = "disconnected"
            all_healthy = False
    except Exception as e:
        checks["neo4j"] = f"unhealthy: {str(e)[:50]}"
        all_healthy = False

    status_code = 200 if all_healthy else 503
    from fastapi.responses import JSONResponse
    return JSONResponse(
        status_code=status_code,
        content={
            "status": "healthy" if all_healthy else "unhealthy",
            "checks": checks,
        }
    )


@app.get("/health/live")
async def health_live():
    """Liveness check - verifies the service is running."""
    return {"status": "alive"}


# =============================================================================
# METRICS ENDPOINT
# =============================================================================
@app.get("/metrics")
async def metrics():
    """Prometheus-compatible metrics endpoint."""
    import time

    # Collect metrics
    metrics_data = []

    # Request metrics from rate limiter
    total_tracked_ips = len(rate_limiter.requests)
    total_requests = sum(len(reqs) for reqs in rate_limiter.requests.values())

    metrics_data.append(f"# HELP storm_logos_rate_limit_tracked_ips Number of IPs being tracked")
    metrics_data.append(f"# TYPE storm_logos_rate_limit_tracked_ips gauge")
    metrics_data.append(f"storm_logos_rate_limit_tracked_ips {total_tracked_ips}")

    metrics_data.append(f"# HELP storm_logos_requests_last_minute Total requests in last minute")
    metrics_data.append(f"# TYPE storm_logos_requests_last_minute gauge")
    metrics_data.append(f"storm_logos_requests_last_minute {total_requests}")

    # Service info
    metrics_data.append(f"# HELP storm_logos_info Service information")
    metrics_data.append(f"# TYPE storm_logos_info gauge")
    metrics_data.append(f'storm_logos_info{{version="1.0.0",environment="{os.environ.get("ENVIRONMENT", "development")}"}} 1')

    # Database connectivity
    try:
        data = get_semantic_data()
        postgres_up = 1 if data and data.n_coordinates > 0 else 0
    except:
        postgres_up = 0

    try:
        ug = get_user_graph()
        neo4j_up = 1 if ug._connected else 0
    except:
        neo4j_up = 0

    metrics_data.append(f"# HELP storm_logos_postgres_up PostgreSQL connectivity")
    metrics_data.append(f"# TYPE storm_logos_postgres_up gauge")
    metrics_data.append(f"storm_logos_postgres_up {postgres_up}")

    metrics_data.append(f"# HELP storm_logos_neo4j_up Neo4j connectivity")
    metrics_data.append(f"# TYPE storm_logos_neo4j_up gauge")
    metrics_data.append(f"storm_logos_neo4j_up {neo4j_up}")

    # Uptime
    metrics_data.append(f"# HELP storm_logos_start_time_seconds Service start time")
    metrics_data.append(f"# TYPE storm_logos_start_time_seconds gauge")
    metrics_data.append(f"storm_logos_start_time_seconds {time.time()}")

    from fastapi.responses import PlainTextResponse
    return PlainTextResponse(
        content="\n".join(metrics_data) + "\n",
        media_type="text/plain; version=0.0.4"
    )


@app.get("/info")
async def info():
    """Get API info including model."""
    engine = get_dream_engine()
    return {
        "service": "storm-logos",
        "model": engine.model,
        "status": "running",
    }


@app.get("/corpus/books")
async def get_corpus_books():
    """Get list of processed books in corpus."""
    try:
        from storm_logos.data.neo4j import get_neo4j
        neo4j = get_neo4j()
        if not neo4j.connect():
            return {"books": [], "total": 0, "error": "Neo4j not connected"}

        # Try to get Book nodes directly first
        detailed_books = []
        with neo4j._driver.session() as session:
            # Query all Book nodes
            query = """
            MATCH (b:Book)
            OPTIONAL MATCH (b)-[:CONTAINS]->(bond:Bond)
            RETURN b.id as id, b.title as title, b.author as author,
                   b.genre as genre, count(bond) as n_bonds
            ORDER BY b.author, b.title
            """
            result = session.run(query)
            for record in result:
                book_id = record["id"] or "unknown"
                detailed_books.append({
                    "id": book_id,
                    "title": record["title"] or book_id.replace("_", " ").title() if book_id else "Unknown",
                    "author": record["author"] or "Unknown",
                    "n_bonds": record["n_bonds"] or 0,
                    "genre": record["genre"] or ""
                })

        # If no Book nodes, check FOLLOWS edges for book IDs
        if not detailed_books:
            books = neo4j.get_books()
            for book_id in books:
                if book_id:
                    detailed_books.append({
                        "id": book_id,
                        "title": book_id.replace("_", " ").title(),
                        "author": "Unknown",
                        "n_bonds": 0,
                        "genre": ""
                    })

        return {"books": detailed_books, "total": len(detailed_books)}
    except Exception as e:
        import traceback
        return {"books": [], "total": 0, "error": str(e), "trace": traceback.format_exc()}


@app.post("/corpus/process")
async def process_book_text(
    data: dict,
    superuser: dict = Depends(get_superuser)
):
    """Process book text and load into corpus. Requires superuser.

    Only superusers can add books to the corpus.
    """
    text = data.get("text", "")
    title = data.get("title", "Untitled")
    author = data.get("author", "Unknown")

    if not text or len(text) < 100:
        return {"error": "Text too short (min 100 chars)"}

    try:
        from storm_logos.data.book_parser import BookParser
        from storm_logos.data.neo4j import get_neo4j
        from storm_logos.data.postgres import get_data

        # Parse text
        parser = BookParser()
        parsed = parser.parse_text(text, title=title, author=author)

        if not parsed.bonds:
            return {"error": "No bonds extracted from text"}

        # Get coordinates
        data_layer = get_data()
        bonds_with_coords = []
        for eb in parsed.bonds:
            bond_id = f"{eb.adj}_{eb.noun}"
            adj_coords = data_layer.get(eb.adj)
            noun_coords = data_layer.get(eb.noun)

            if adj_coords and noun_coords:
                from storm_logos.data.models import Bond
                bond = Bond(
                    id=bond_id,
                    adj=eb.adj,
                    noun=eb.noun,
                    A=(adj_coords.A + noun_coords.A) / 2,
                    S=(adj_coords.S + noun_coords.S) / 2,
                    tau=(adj_coords.tau + noun_coords.tau) / 2
                )
                bonds_with_coords.append((eb, bond))

        # Store in Neo4j
        neo4j = get_neo4j()
        if not neo4j.connect():
            return {"error": "Neo4j not connected"}

        book_id = f"{author.lower().replace(' ', '_')}_{title.lower().replace(' ', '_')}"

        with neo4j._driver.session() as session:
            # Create author and book nodes
            session.run("""
                MERGE (a:Author {name: $author})
                MERGE (b:Book {id: $book_id})
                SET b.title = $title, b.author = $author,
                    b.n_bonds = $n_bonds, b.n_sentences = $n_sentences
                MERGE (a)-[:WROTE]->(b)
            """, author=author, book_id=book_id, title=title,
                n_bonds=len(bonds_with_coords), n_sentences=parsed.n_sentences)

            # Create bonds and FOLLOWS edges
            prev_bond_id = None
            for i, (eb, bond) in enumerate(bonds_with_coords):
                session.run("""
                    MERGE (bond:Bond {id: $bond_id})
                    SET bond.adj = $adj, bond.noun = $noun,
                        bond.A = $A, bond.S = $S, bond.tau = $tau
                    WITH bond
                    MATCH (b:Book {id: $book_id})
                    MERGE (b)-[:CONTAINS {chapter: $chapter, sentence: $sentence}]->(bond)
                """, bond_id=bond.id, adj=bond.adj, noun=bond.noun,
                    A=bond.A, S=bond.S, tau=bond.tau,
                    book_id=book_id, chapter=eb.chapter, sentence=eb.sentence)

                # Create FOLLOWS edge
                if prev_bond_id:
                    session.run("""
                        MATCH (b1:Bond {id: $prev_id}), (b2:Bond {id: $curr_id})
                        MERGE (b1)-[:FOLLOWS {book_id: $book_id, weight: 1.0}]->(b2)
                    """, prev_id=prev_bond_id, curr_id=bond.id, book_id=book_id)

                prev_bond_id = bond.id

        return {
            "success": True,
            "book_id": book_id,
            "title": title,
            "author": author,
            "n_bonds": len(bonds_with_coords),
            "n_sentences": parsed.n_sentences
        }

    except Exception as e:
        import traceback
        return {"error": str(e), "trace": traceback.format_exc()}


# =============================================================================
# ADMIN ENDPOINTS
# =============================================================================
@app.get("/admin/users")
async def get_admin_users(
    superuser: dict = Depends(get_superuser)
):
    """Get all users with activity statistics. Superuser only."""
    try:
        ug = get_user_graph()
        users = ug.get_all_users_stats()

        # Calculate summary stats
        total_users = len(users)
        verified_users = sum(1 for u in users if u.get("email_verified"))
        total_sessions = sum(u.get("session_count", 0) for u in users)
        total_dreams = sum(u.get("dream_count", 0) for u in users)

        return {
            "users": users,
            "summary": {
                "total_users": total_users,
                "verified_users": verified_users,
                "unverified_users": total_users - verified_users,
                "total_sessions": total_sessions,
                "total_dreams": total_dreams,
                "total_activity": total_sessions + total_dreams,
            }
        }
    except Exception as e:
        import traceback
        return {"users": [], "summary": {}, "error": str(e), "trace": traceback.format_exc()}


@app.post("/dreams/analyze")
async def analyze_dream(
    data: dict,
    request: Request,
    current_user: Optional[dict] = Depends(get_optional_user)
):
    """Quick dream analysis without conversation.

    Returns symbols, archetypes, interpretation, and corpus resonances.
    Guest users limited to 3 analyses. Authenticated users unlimited.
    """
    from .rate_limiter import get_rate_limiter

    dream_text = data.get("dream", "").strip()

    if not dream_text or len(dream_text) < 20:
        return {"error": "Dream text too short (min 20 chars)"}

    # Check guest limit (authenticated users bypass)
    if not current_user:
        limiter = get_rate_limiter()
        allowed, info = limiter.check_guest_dream_limit(request)
        if not allowed:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Guest limit reached ({info['limit']} analyses). Please register for unlimited access.",
                headers={"X-Guest-Limit": str(info['limit']), "X-Guest-Used": str(info['used'])}
            )

    try:
        engine = get_dream_engine()
        analysis = engine.analyze(dream_text)

        # Format symbols
        symbols = []
        for s in analysis.symbols:
            symbols.append({
                "text": s.raw_text,
                "archetype": s.archetype or "",
                "interpretation": s.interpretation or "",
                "A": s.bond.A,
                "S": s.bond.S,
                "tau": s.bond.tau,
                "corpus_sources": s.corpus_sources or [],
            })

        # Get archetype scores
        state = analysis.state
        archetypes = {
            "shadow": state.shadow,
            "anima_animus": state.anima_animus,
            "self": state.self_archetype,
            "mother": state.mother,
            "father": state.father,
            "hero": state.hero,
            "trickster": state.trickster,
            "death_rebirth": state.death_rebirth,
        }

        dominant, score = state.dominant_archetype()

        # Increment guest count after successful analysis
        guest_info = None
        if not current_user:
            limiter = get_rate_limiter()
            count = limiter.increment_guest_dream_count(request)
            guest_info = {
                "used": count,
                "remaining": max(0, 3 - count),
                "limit": 3,
            }

        result = {
            "dream": dream_text,
            "symbols": symbols,
            "archetypes": archetypes,
            "dominant_archetype": dominant,
            "dominant_score": score,
            "coordinates": {
                "A": state.A,
                "S": state.S,
                "tau": state.tau,
            },
            "markers": {
                "transformation": state.transformation,
                "journey": state.journey,
                "confrontation": state.confrontation,
            },
            "interpretation": analysis.interpretation,
            "corpus_resonances": analysis.corpus_resonances,
            "timestamp": analysis.timestamp,
        }

        if guest_info:
            result["guest_limit"] = guest_info

        return result

    except Exception as e:
        import traceback
        return {"error": str(e), "trace": traceback.format_exc()}


@app.post("/dreams/save")
async def save_dream(
    data: dict,
    current_user: dict = Depends(get_current_user)
):
    """Save a dream analysis to user's collection."""
    from datetime import datetime

    dream_text = data.get("dream", "").strip()
    interpretation = data.get("interpretation", "")
    symbols = data.get("symbols", [])
    archetypes = data.get("archetypes", {})
    dominant = data.get("dominant_archetype", "")
    title = data.get("title", "")

    if not dream_text:
        return {"error": "No dream text provided"}

    try:
        ug = get_user_graph()
        dream_id = datetime.now().strftime("%Y%m%d_%H%M%S")

        # Save to Neo4j
        with ug._neo4j._driver.session() as session:
            session.run("""
                MATCH (u:User {user_id: $user_id})
                CREATE (d:Dream {
                    id: $dream_id,
                    title: $title,
                    text: $dream_text,
                    interpretation: $interpretation,
                    dominant_archetype: $dominant,
                    timestamp: $timestamp
                })
                CREATE (u)-[:DREAMED]->(d)
                WITH d
                UNWIND $symbols as sym
                MERGE (s:DreamSymbol {text: sym.text})
                SET s.archetype = sym.archetype, s.A = sym.A, s.S = sym.S
                CREATE (d)-[:CONTAINS_SYMBOL]->(s)
            """,
                user_id=current_user["user_id"],
                dream_id=dream_id,
                title=title or f"Dream {dream_id}",
                dream_text=dream_text[:2000],
                interpretation=interpretation[:3000],
                dominant=dominant,
                timestamp=datetime.now().isoformat(),
                symbols=symbols[:20]
            )

        return {
            "success": True,
            "dream_id": dream_id,
            "message": "Dream saved"
        }

    except Exception as e:
        import traceback
        return {"error": str(e), "trace": traceback.format_exc()}


@app.get("/dreams/list")
async def list_dreams(
    current_user: dict = Depends(get_current_user)
):
    """Get user's saved dreams."""
    try:
        ug = get_user_graph()

        with ug._neo4j._driver.session() as session:
            result = session.run("""
                MATCH (u:User {user_id: $user_id})-[:DREAMED]->(d:Dream)
                OPTIONAL MATCH (d)-[:CONTAINS_SYMBOL]->(s:DreamSymbol)
                WITH d, collect(DISTINCT {text: s.text, archetype: s.archetype}) as symbols
                RETURN d.id as id, d.title as title, d.text as text,
                       d.interpretation as interpretation,
                       d.dominant_archetype as dominant_archetype,
                       d.timestamp as timestamp, symbols
                ORDER BY d.timestamp DESC
            """, user_id=current_user["user_id"])

            dreams = []
            for record in result:
                dreams.append({
                    "id": record["id"],
                    "title": record["title"],
                    "text": record["text"][:200] + "..." if len(record["text"] or "") > 200 else record["text"],
                    "interpretation": record["interpretation"],
                    "dominant_archetype": record["dominant_archetype"],
                    "timestamp": record["timestamp"],
                    "symbols": [s for s in record["symbols"] if s.get("text")],
                })

        return {"dreams": dreams, "total": len(dreams)}

    except Exception as e:
        import traceback
        return {"dreams": [], "total": 0, "error": str(e)}


@app.delete("/dreams/{dream_id}")
async def delete_dream(
    dream_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Delete a saved dream."""
    try:
        ug = get_user_graph()

        with ug._neo4j._driver.session() as session:
            result = session.run("""
                MATCH (u:User {user_id: $user_id})-[:DREAMED]->(d:Dream {id: $dream_id})
                DETACH DELETE d
                RETURN count(d) as deleted
            """, user_id=current_user["user_id"], dream_id=dream_id)

            deleted = result.single()["deleted"]

        if deleted > 0:
            return {"success": True, "message": "Dream deleted"}
        else:
            return {"error": "Dream not found"}

    except Exception as e:
        return {"error": str(e)}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
