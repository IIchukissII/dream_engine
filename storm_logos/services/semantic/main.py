"""Semantic Microservice: Dedicated semantic analysis and processing.

This microservice handles all semantic operations:
- Storm: Candidate explosion from Neo4j and spatial neighbors
- Dialectic: Thesis-antithesis filtering
- Chain: Resonance-based selection
- Physics: RC dynamics, gravity, Boltzmann factors
- Metrics: Coherence, irony, tension, defense analysis
- Archetype: Jungian archetype detection

Run with:
    uvicorn storm_logos.services.semantic.main:app --port 8002
"""

import os
import sys
import time
from pathlib import Path
from typing import Optional, Dict, Any, List
from datetime import datetime
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, status, Request, Response
from pydantic import BaseModel
from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST

# Ensure storm_logos is importable
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from storm_logos.data.postgres import get_data
from storm_logos.data.neo4j import get_neo4j
from storm_logos.data.models import Bond, SemanticState
from storm_logos.metrics.engine import MetricsEngine
from storm_logos.semantic.storm import Storm
from storm_logos.semantic.dialectic import Dialectic
from storm_logos.semantic.chain import Chain
from storm_logos.semantic.physics import (
    gravity_potential, gravity_force, rc_update, coherence,
    boltzmann_factor, transition_probability, master_score
)
from storm_logos.metrics.analyzers.archetype import get_archetype_analyzer


# =============================================================================
# PROMETHEUS METRICS
# =============================================================================

REQUEST_COUNT = Counter(
    'semantic_requests_total',
    'Total requests to semantic service',
    ['endpoint', 'status']
)

REQUEST_LATENCY = Histogram(
    'semantic_request_latency_seconds',
    'Request latency in seconds',
    ['endpoint'],
    buckets=[0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0]
)

COORDINATES_LOADED = Gauge(
    'semantic_coordinates_loaded',
    'Number of word coordinates loaded'
)

NEO4J_CONNECTED = Gauge(
    'semantic_neo4j_connected',
    'Whether Neo4j is connected (1=yes, 0=no)'
)

ACTIVE_REQUESTS = Gauge(
    'semantic_active_requests',
    'Number of currently active requests'
)


# =============================================================================
# MODELS
# =============================================================================

class CoordinatesRequest(BaseModel):
    """Request for word coordinates."""
    words: List[str]


class CoordinatesResponse(BaseModel):
    """Response with word coordinates."""
    coordinates: Dict[str, Dict[str, float]]
    found: int
    missing: List[str]


class MetricsRequest(BaseModel):
    """Request for text metrics."""
    text: str


class MetricsResponse(BaseModel):
    """Response with text metrics."""
    coherence: float
    irony: float
    tension: float
    tau_mean: float
    tau_variance: float
    A_position: float
    S_position: float
    defenses: List[str]


class DialecticRequest(BaseModel):
    """Request for dialectic analysis."""
    A: float
    S: float
    tau: float = 2.5
    irony: float = 0.0


class DialecticResponse(BaseModel):
    """Response with dialectic analysis."""
    thesis: Dict[str, Any]
    antithesis: Dict[str, Any]
    synthesis: Dict[str, Any]
    tension: float
    intervention: Dict[str, Any]


class StormRequest(BaseModel):
    """Request for Storm candidate explosion."""
    A: float
    S: float
    tau: float = 2.5
    radius: float = 1.0
    max_candidates: int = 50


class StormResponse(BaseModel):
    """Response with Storm candidates."""
    candidates: List[Dict[str, Any]]
    count: int
    sources: Dict[str, int]


class ArchetypeRequest(BaseModel):
    """Request for archetype detection."""
    text: str
    symbols: Optional[List[Dict[str, float]]] = None


class ArchetypeResponse(BaseModel):
    """Response with archetype scores."""
    archetypes: Dict[str, float]
    dominant: str
    dominant_score: float
    symbols: List[Dict[str, Any]]


class PhysicsRequest(BaseModel):
    """Request for physics calculations."""
    current_A: float
    current_S: float
    current_tau: float
    target_A: float
    target_S: float
    target_tau: float
    dt: float = 0.1
    decay: float = 0.05


class PhysicsResponse(BaseModel):
    """Response with physics calculations."""
    new_state: Dict[str, float]
    gravity_potential: float
    gravity_force: Dict[str, float]


class HealthResponse(BaseModel):
    """Health check response."""
    status: str
    service: str
    coordinates_loaded: int
    neo4j_connected: bool
    timestamp: str


# =============================================================================
# SERVICE STATE
# =============================================================================

class SemanticService:
    """Manages semantic processing components."""

    def __init__(self):
        self._data = None
        self._neo4j = None
        self._metrics = None
        self._storm = None
        self._dialectic = None
        self._chain = None
        self._archetype = None

    def initialize(self):
        """Initialize all components."""
        print("  Loading semantic data...")
        self._data = get_data()
        print(f"    {self._data.n_coordinates:,} coordinates")

        print("  Connecting to Neo4j...")
        self._neo4j = get_neo4j()
        if self._neo4j.connect():
            print("    Connected")
        else:
            print("    Warning: Neo4j not connected")

        print("  Initializing components...")
        self._metrics = MetricsEngine()
        self._storm = Storm()
        self._dialectic = Dialectic()
        self._chain = Chain()
        self._archetype = get_archetype_analyzer()

    @property
    def data(self):
        return self._data

    @property
    def neo4j(self):
        return self._neo4j

    @property
    def metrics(self):
        return self._metrics

    @property
    def storm(self):
        return self._storm

    @property
    def dialectic(self):
        return self._dialectic

    @property
    def chain(self):
        return self._chain

    @property
    def archetype(self):
        return self._archetype


_service: Optional[SemanticService] = None


def get_service() -> SemanticService:
    """Get singleton service instance."""
    global _service
    if _service is None:
        _service = SemanticService()
    return _service


# =============================================================================
# LIFESPAN
# =============================================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize service on startup."""
    print("Starting Semantic Microservice...")

    service = get_service()
    service.initialize()

    print("Semantic Microservice ready!")

    yield

    print("Shutting down Semantic Microservice...")


# =============================================================================
# APP
# =============================================================================

app = FastAPI(
    title="Storm-Logos Semantic Service",
    description="""
Dedicated microservice for semantic analysis and processing.

## Features

- **Coordinates**: Word coordinate lookup in 3D semantic space (A, S, tau)
- **Metrics**: Text analysis for coherence, irony, tension, defenses
- **Dialectic**: Thesis-antithesis-synthesis analysis
- **Storm**: Candidate explosion from corpus
- **Physics**: RC dynamics, gravity, transition probabilities
- **Archetypes**: Jungian archetype detection

## Semantic Space

- **A (Affirmation)**: -1 (negative) to +1 (positive)
- **S (Sacred)**: -1 (mundane) to +1 (sacred/elevated)
- **tau (Abstraction)**: 0.5 (concrete) to 4.5 (abstract)
""",
    version="1.0.0",
    lifespan=lifespan,
)


# =============================================================================
# MIDDLEWARE FOR METRICS
# =============================================================================

@app.middleware("http")
async def metrics_middleware(request: Request, call_next):
    """Track request metrics."""
    if request.url.path == "/metrics":
        return await call_next(request)

    endpoint = request.url.path
    ACTIVE_REQUESTS.inc()
    start_time = time.time()

    try:
        response = await call_next(request)
        REQUEST_COUNT.labels(endpoint=endpoint, status=response.status_code).inc()
        return response
    except Exception as e:
        REQUEST_COUNT.labels(endpoint=endpoint, status=500).inc()
        raise
    finally:
        REQUEST_LATENCY.labels(endpoint=endpoint).observe(time.time() - start_time)
        ACTIVE_REQUESTS.dec()


# =============================================================================
# ENDPOINTS
# =============================================================================

@app.get("/metrics")
async def prometheus_metrics():
    """Prometheus metrics endpoint."""
    service = get_service()

    # Update gauges
    if service.data:
        COORDINATES_LOADED.set(service.data.n_coordinates)
    if service.neo4j:
        NEO4J_CONNECTED.set(1 if service.neo4j._connected else 0)

    return Response(
        content=generate_latest(),
        media_type=CONTENT_TYPE_LATEST
    )


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    service = get_service()
    return HealthResponse(
        status="healthy",
        service="semantic",
        coordinates_loaded=service.data.n_coordinates if service.data else 0,
        neo4j_connected=service.neo4j._connected if service.neo4j else False,
        timestamp=datetime.now().isoformat(),
    )


@app.post("/coordinates", response_model=CoordinatesResponse)
async def get_coordinates(request: CoordinatesRequest):
    """Get semantic coordinates for words."""
    service = get_service()

    if not service.data:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Semantic data not loaded"
        )

    coordinates = {}
    missing = []

    for word in request.words:
        coords = service.data.get(word.lower())
        if coords:
            coordinates[word] = {
                "A": coords.A,
                "S": coords.S,
                "tau": coords.tau,
            }
        else:
            missing.append(word)

    return CoordinatesResponse(
        coordinates=coordinates,
        found=len(coordinates),
        missing=missing,
    )


@app.post("/metrics", response_model=MetricsResponse)
async def analyze_metrics(request: MetricsRequest):
    """Analyze text for semantic metrics."""
    service = get_service()

    if not service.metrics:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Metrics engine not initialized"
        )

    try:
        metrics = service.metrics.measure(text=request.text)

        return MetricsResponse(
            coherence=metrics.coherence,
            irony=metrics.irony,
            tension=metrics.tension_score,
            tau_mean=metrics.tau_mean,
            tau_variance=metrics.tau_variance,
            A_position=metrics.A_position,
            S_position=metrics.S_position,
            defenses=metrics.defenses,
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Metrics analysis error: {str(e)}"
        )


@app.post("/dialectic", response_model=DialecticResponse)
async def analyze_dialectic(request: DialecticRequest):
    """Perform dialectic analysis on semantic position."""
    service = get_service()

    if not service.dialectic:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Dialectic engine not initialized"
        )

    try:
        state = SemanticState(
            A=request.A,
            S=request.S,
            tau=request.tau,
            irony=request.irony,
        )

        analysis = service.dialectic.analyze(state)

        return DialecticResponse(
            thesis=analysis.get("thesis", {}),
            antithesis=analysis.get("antithesis", {}),
            synthesis=analysis.get("synthesis", {}),
            tension=analysis.get("tension", 0.0),
            intervention=analysis.get("intervention", {}),
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Dialectic analysis error: {str(e)}"
        )


@app.post("/storm", response_model=StormResponse)
async def explode_candidates(request: StormRequest):
    """Generate candidate bonds using Storm algorithm."""
    service = get_service()

    if not service.storm:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Storm engine not initialized"
        )

    try:
        state = SemanticState(A=request.A, S=request.S, tau=request.tau)

        candidates = service.storm.explode(
            Q=state,
            radius=request.radius,
            max_candidates=request.max_candidates,
        )

        # Convert to response format
        candidates_list = []
        for bond in candidates[:request.max_candidates]:
            candidates_list.append({
                "text": bond.text,
                "A": bond.A,
                "S": bond.S,
                "tau": bond.tau,
                "variety": bond.variety,
            })

        return StormResponse(
            candidates=candidates_list,
            count=len(candidates_list),
            sources={"spatial": len(candidates_list)},  # Simplified
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Storm explosion error: {str(e)}"
        )


@app.post("/archetypes", response_model=ArchetypeResponse)
async def detect_archetypes(request: ArchetypeRequest):
    """Detect Jungian archetypes in text."""
    service = get_service()

    if not service.archetype:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Archetype analyzer not initialized"
        )

    try:
        # Analyze text for archetypes
        scores = service.archetype.analyze_text(request.text)

        # Find dominant
        dominant = max(scores.items(), key=lambda x: x[1]) if scores else ("unknown", 0.0)

        # Process symbols if provided
        symbols = []
        if request.symbols:
            for sym in request.symbols:
                bond = Bond(
                    noun=sym.get("text", ""),
                    A=sym.get("A", 0),
                    S=sym.get("S", 0),
                    tau=sym.get("tau", 2.5),
                )
                arch, interp = service.archetype.get_symbol_interpretation(bond)
                symbols.append({
                    "text": bond.noun,
                    "archetype": arch,
                    "interpretation": interp,
                    "A": bond.A,
                    "S": bond.S,
                })

        return ArchetypeResponse(
            archetypes=scores,
            dominant=dominant[0],
            dominant_score=dominant[1],
            symbols=symbols,
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Archetype detection error: {str(e)}"
        )


@app.post("/physics", response_model=PhysicsResponse)
async def calculate_physics(request: PhysicsRequest):
    """Calculate semantic physics (RC update, gravity)."""
    try:
        current = SemanticState(
            A=request.current_A,
            S=request.current_S,
            tau=request.current_tau,
        )
        target = SemanticState(
            A=request.target_A,
            S=request.target_S,
            tau=request.target_tau,
        )

        # RC update
        new_state = rc_update(current, target, dt=request.dt, decay=request.decay)

        # Gravity
        grav_pot = gravity_potential(current)
        grav_force = gravity_force(current)

        return PhysicsResponse(
            new_state={
                "A": new_state.A,
                "S": new_state.S,
                "tau": new_state.tau,
            },
            gravity_potential=grav_pot,
            gravity_force={
                "dA": grav_force[0],
                "dS": grav_force[1],
                "dtau": grav_force[2],
            },
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Physics calculation error: {str(e)}"
        )


@app.get("/info")
async def get_info():
    """Get service information."""
    service = get_service()
    return {
        "service": "semantic",
        "coordinates": service.data.n_coordinates if service.data else 0,
        "neo4j_connected": service.neo4j._connected if service.neo4j else False,
        "components": ["metrics", "storm", "dialectic", "chain", "archetype", "physics"],
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)
