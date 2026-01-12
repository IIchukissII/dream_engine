"""Therapist Microservice: Dedicated therapy processing with full theory.

This microservice handles all therapy-related processing using the complete
Storm-Logos theoretical framework:
- MetricsEngine for semantic analysis
- FeedbackEngine for homeostatic targets
- AdaptiveController for PI control
- Dialectic for thesis-antithesis filtering
- RC-circuit dynamics for state evolution

Run with:
    uvicorn storm_logos.services.therapist.main:app --port 8001
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

from storm_logos.applications import Therapist
from storm_logos.data.models import SemanticState


# =============================================================================
# PROMETHEUS METRICS
# =============================================================================

REQUEST_COUNT = Counter(
    'therapist_requests_total',
    'Total requests to therapist service',
    ['endpoint', 'status']
)

REQUEST_LATENCY = Histogram(
    'therapist_request_latency_seconds',
    'Request latency in seconds',
    ['endpoint'],
    buckets=[0.1, 0.5, 1.0, 2.5, 5.0, 10.0, 30.0, 60.0]
)

ACTIVE_SESSIONS = Gauge(
    'therapist_active_sessions',
    'Number of active therapy sessions'
)

ACTIVE_REQUESTS = Gauge(
    'therapist_active_requests',
    'Number of currently active requests'
)

THERAPY_TURNS = Counter(
    'therapist_turns_total',
    'Total therapy turns processed'
)


# =============================================================================
# MODELS
# =============================================================================

class TherapyRequest(BaseModel):
    """Request for therapy processing."""
    text: str
    session_id: Optional[str] = None
    context: Optional[Dict[str, Any]] = None


class TherapyResponse(BaseModel):
    """Response from therapy processing."""
    response: str
    semantic_state: Dict[str, float]
    dialectic: Dict[str, Any]
    metrics: Dict[str, Any]
    defenses: List[str]
    session_id: str


class AnalysisRequest(BaseModel):
    """Request for text analysis without response generation."""
    text: str


class AnalysisResponse(BaseModel):
    """Response from text analysis."""
    semantic_state: Dict[str, float]
    dialectic: Dict[str, Any]
    metrics: Dict[str, Any]
    defenses: List[str]


class HealthResponse(BaseModel):
    """Health check response."""
    status: str
    service: str
    model: str
    timestamp: str


# =============================================================================
# SERVICE STATE
# =============================================================================

class TherapistService:
    """Manages Therapist instances per session."""

    def __init__(self):
        self.model = os.environ.get("LLM_MODEL", "groq:llama-3.3-70b-versatile")
        self._sessions: Dict[str, Therapist] = {}
        self._default_therapist: Optional[Therapist] = None

    def get_therapist(self, session_id: Optional[str] = None) -> Therapist:
        """Get or create therapist for session."""
        if session_id:
            if session_id not in self._sessions:
                self._sessions[session_id] = Therapist(model=self.model)
            return self._sessions[session_id]

        if self._default_therapist is None:
            self._default_therapist = Therapist(model=self.model)
        return self._default_therapist

    def reset_session(self, session_id: str):
        """Reset a session's therapist."""
        if session_id in self._sessions:
            self._sessions[session_id].reset()
            del self._sessions[session_id]

    def cleanup_old_sessions(self, max_age_hours: int = 24):
        """Remove old inactive sessions."""
        # In production, implement proper session timeout
        pass


_service: Optional[TherapistService] = None


def get_service() -> TherapistService:
    """Get singleton service instance."""
    global _service
    if _service is None:
        _service = TherapistService()
    return _service


# =============================================================================
# LIFESPAN
# =============================================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize service on startup."""
    print("Starting Therapist Microservice...")

    service = get_service()
    print(f"  Model: {service.model}")

    # Warm up with a test therapist
    print("  Initializing default therapist...")
    _ = service.get_therapist()

    print("Therapist Microservice ready!")

    yield

    print("Shutting down Therapist Microservice...")


# =============================================================================
# APP
# =============================================================================

app = FastAPI(
    title="Storm-Logos Therapist Service",
    description="""
Dedicated microservice for therapy processing using the full Storm-Logos theory.

## Features

- **Full Theory Pipeline**: MetricsEngine → FeedbackEngine → AdaptiveController → Dialectic
- **RC-Circuit Dynamics**: State evolution with proper charge/decay
- **Defense Detection**: Identifies psychological defenses in text
- **Dialectic Analysis**: Thesis-antithesis filtering for interventions

## Endpoints

- `POST /process`: Process patient text and generate therapeutic response
- `POST /analyze`: Analyze text without generating response
- `POST /reset/{session_id}`: Reset session state
- `GET /health`: Health check
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
    ACTIVE_SESSIONS.set(len(service._sessions))

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
        service="therapist",
        model=service.model,
        timestamp=datetime.now().isoformat(),
    )


@app.post("/process", response_model=TherapyResponse)
async def process_therapy(request: TherapyRequest):
    """Process patient text and generate therapeutic response.

    Uses the full Storm-Logos pipeline:
    1. MetricsEngine analyzes semantic position
    2. FeedbackEngine computes homeostatic errors
    3. AdaptiveController adapts parameters via PI control
    4. Dialectic computes thesis-antithesis-synthesis
    5. LLM generates response informed by semantic analysis
    6. RC-dynamics update state trajectory
    """
    service = get_service()
    session_id = request.session_id or datetime.now().strftime("%Y%m%d_%H%M%S")

    therapist = service.get_therapist(session_id)

    try:
        # Generate response using full pipeline
        response = therapist.respond(request.text)
        THERAPY_TURNS.inc()

        # Get trajectory and state
        trajectory = therapist.get_trajectory()
        current_state = trajectory.current

        # Get dialectic analysis
        dial = {}
        if current_state:
            dial = therapist.dialectic.analyze(current_state)

        # Get metrics from last turn
        metrics_data = {}
        defenses = []
        if therapist._turns:
            last_turn = therapist._turns[-1]
            metrics_data = last_turn.get('metrics', {})
            defenses = metrics_data.get('defenses', [])

        # Build semantic state dict
        state_dict = {
            "A": current_state.A if current_state else 0.0,
            "S": current_state.S if current_state else 0.0,
            "tau": current_state.tau if current_state else 2.5,
            "irony": current_state.irony if current_state else 0.0,
        }

        return TherapyResponse(
            response=response,
            semantic_state=state_dict,
            dialectic=dial,
            metrics=metrics_data,
            defenses=defenses,
            session_id=session_id,
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Therapy processing error: {str(e)}"
        )


@app.post("/analyze", response_model=AnalysisResponse)
async def analyze_text(request: AnalysisRequest):
    """Analyze text without generating a response.

    Returns semantic state, dialectic analysis, and metrics
    without invoking the LLM for response generation.
    """
    service = get_service()
    therapist = service.get_therapist()

    try:
        # Use metrics engine directly
        metrics = therapist.metrics.measure(text=request.text)

        # Create state from metrics
        state = SemanticState(
            A=metrics.A_position,
            S=metrics.S_position,
            irony=metrics.irony,
        )

        # Get dialectic analysis
        dial = therapist.dialectic.analyze(state)

        # Build state dict
        state_dict = {
            "A": state.A,
            "S": state.S,
            "tau": state.tau,
            "irony": state.irony,
        }

        # Build metrics dict
        metrics_dict = {
            "coherence": metrics.coherence,
            "tension": metrics.tension_score,
            "tau_mean": metrics.tau_mean,
            "tau_variance": metrics.tau_variance,
        }

        return AnalysisResponse(
            semantic_state=state_dict,
            dialectic=dial,
            metrics=metrics_dict,
            defenses=metrics.defenses,
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Analysis error: {str(e)}"
        )


@app.post("/reset/{session_id}")
async def reset_session(session_id: str):
    """Reset a therapy session."""
    service = get_service()
    service.reset_session(session_id)
    return {"message": f"Session {session_id} reset", "session_id": session_id}


@app.get("/sessions")
async def list_sessions():
    """List active therapy sessions."""
    service = get_service()
    sessions = []
    for sid, therapist in service._sessions.items():
        sessions.append({
            "session_id": sid,
            "turns": len(therapist._turns),
            "model": therapist.model,
        })
    return {"sessions": sessions, "total": len(sessions)}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
