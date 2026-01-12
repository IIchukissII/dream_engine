"""API Models: Pydantic models for request/response."""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime

# Import canonical SessionMode from data models
from storm_logos.data.models import SessionMode

__all__ = [
    # Re-exported
    'SessionMode',
    # Auth
    'UserCreate', 'UserLogin', 'UserResponse', 'TokenResponse',
    # Sessions
    'SessionStart', 'SessionMessage', 'SessionResponse', 'SessionEnd',
    # Archetypes
    'ArchetypeManifestationResponse', 'ArchetypeEvolution', 'UserProfile', 'SessionHistory',
    # Dream Analysis
    'DreamAnalysisRequest', 'DreamSymbolResponse', 'DreamAnalysisResponse',
]


# =============================================================================
# AUTH
# =============================================================================

class UserCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=6)


class UserLogin(BaseModel):
    username: str
    password: str


class UserResponse(BaseModel):
    user_id: str
    username: str
    created_at: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


# =============================================================================
# SESSIONS
# =============================================================================

class SessionStart(BaseModel):
    mode: Optional[SessionMode] = None


class SessionMessage(BaseModel):
    message: str
    mode: Optional[str] = None  # "dream", "therapy", or "auto" for hybrid


class SessionResponse(BaseModel):
    session_id: str
    mode: SessionMode
    turn: int
    response: str
    symbols: List[Dict[str, Any]] = []
    emotions: List[str] = []
    themes: List[str] = []


class SessionEnd(BaseModel):
    session_id: str
    turns: int
    mode: str
    symbols: List[Dict[str, Any]]
    emotions: List[str]
    themes: List[str]
    archetypes: List[Dict[str, Any]]
    summary: str


# =============================================================================
# ARCHETYPES
# =============================================================================

# Note: The canonical ArchetypeManifestation dataclass is in storm_logos.data.user_graph
# This is the API response DTO version for serialization

class ArchetypeManifestationResponse(BaseModel):
    """API response model for archetype manifestations."""
    archetype: str
    symbols: List[str]
    emotions: List[str]
    context: str = ""


class ArchetypeEvolution(BaseModel):
    session_id: str
    timestamp: str
    context: str
    symbols: List[str]
    emotions: List[str]


class UserProfile(BaseModel):
    username: str
    total_sessions: int
    archetypes: Dict[str, int]
    dominant_archetypes: List[str]


class SessionHistory(BaseModel):
    session_id: str
    mode: str
    timestamp: str
    summary: str
    archetypes: List[str]


# =============================================================================
# DREAM ANALYSIS
# =============================================================================

class DreamAnalysisRequest(BaseModel):
    dream_text: str


# Note: The canonical DreamSymbol dataclass is in storm_logos.data.models
# This is the API response DTO version with flattened coordinates

class DreamSymbolResponse(BaseModel):
    """API response model for dream symbols (flattened from internal DreamSymbol)."""
    text: str
    archetype: Optional[str] = None
    A: float = 0.0
    S: float = 0.0
    tau: float = 2.5


class DreamAnalysisResponse(BaseModel):
    symbols: List[DreamSymbolResponse]
    archetypes: List[ArchetypeManifestationResponse]
    dominant_archetype: str
    coordinates: Dict[str, float]
    interpretation: str
    corpus_resonances: List[Dict[str, str]] = []
