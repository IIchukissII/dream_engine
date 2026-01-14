"""Sessions Router: Therapy and dream session management.

Now uses the full Storm-Logos theoretical framework:
- Therapist class with MetricsEngine, FeedbackEngine, AdaptiveController
- RC-circuit dynamics for state evolution
- Dialectic analysis for thesis-antithesis filtering
- DreamEngine for symbol extraction in dream mode
"""

import json
import logging
from datetime import datetime
from typing import Optional, Dict, List, Any
from dataclasses import dataclass, field
from fastapi import APIRouter, HTTPException, status, Depends

from storm_logos.data.user_graph import SessionRecord, ArchetypeManifestation as AM

from ..models import (
    SessionStart, SessionMessage, SessionResponse, SessionEnd,
    SessionMode
)
from ..deps import (
    get_current_user, get_optional_user, get_dream_engine, get_user_graph,
    get_session, store_session, remove_session, get_user_active_session,
    get_therapist
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/sessions", tags=["sessions"])


@router.get("/history")
async def get_session_history(
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Get user's session history."""
    ug = get_user_graph()
    sessions = ug.get_user_sessions(current_user["user_id"])
    return {"sessions": sessions}


@dataclass
class SessionState:
    """Active session state with full theory tracking.

    Tracks semantic position using RC-circuit dynamics and
    dialectic analysis for therapeutic direction.
    """
    session_id: str
    user_id: Optional[str]
    mode: str = "hybrid"
    turn: int = 0
    dream_text: Optional[str] = None

    # Semantic state (A, S, tau coordinates)
    A: float = 0.0
    S: float = 0.0
    tau: float = 2.5

    # Psychological markers
    irony: float = 0.0
    defenses: List[str] = field(default_factory=list)

    # Dialectic analysis cache
    thesis_description: str = ""
    antithesis_description: str = ""
    intervention_direction: str = ""

    # Extracted content
    symbols: List[Dict[str, Any]] = field(default_factory=list)
    themes: List[str] = field(default_factory=list)
    emotions: List[str] = field(default_factory=list)

    # Conversation history
    history: List[Dict[str, Any]] = field(default_factory=list)
    started_at: str = ""


def _analyze_input_mode(engine, text: str, current_mode: str) -> Dict[str, Any]:
    """Analyze user input to determine mode and extract basic info.

    Uses LLM for initial classification, but actual therapeutic
    analysis is done by the Therapist class.
    """
    system = """Analyze the user's input in a therapy/dream context. Return JSON:
{
    "type": "greeting|dream_content|association|emotion|question|reflection|goodbye",
    "mode_hint": "dream|therapy|unclear",
    "contains_dream": true/false,
    "emotions_detected": ["list"],
    "key_symbols": ["list"]
}"""

    prompt = f"""Current mode: {current_mode}
User input: "{text}"
Return only valid JSON."""

    try:
        response = engine._call_llm(system, prompt, max_tokens=200)
        if "{" in response:
            json_str = response[response.index("{"):response.rindex("}")+1]
            return json.loads(json_str)
    except (json.JSONDecodeError, ValueError, AttributeError):
        pass

    return {"type": "unclear", "mode_hint": "unclear", "contains_dream": False,
            "emotions_detected": [], "key_symbols": []}


def _generate_therapy_response(therapist, patient_text: str, state: SessionState) -> Dict[str, Any]:
    """Generate response using Therapist class with full theory.

    Uses:
    - MetricsEngine for semantic analysis
    - FeedbackEngine for homeostatic error computation
    - AdaptiveController for PI control
    - Dialectic for thesis-antithesis analysis
    - RC-circuit dynamics via ConversationTrajectory
    """
    # Generate response using the full pipeline
    response = therapist.respond(patient_text)

    # Get the latest state from therapist's trajectory
    trajectory = therapist.get_trajectory()
    current_state = trajectory.current

    # Get dialectic analysis
    dial = therapist.dialectic.analyze(current_state) if current_state else {}

    # Extract metrics from the therapist's last analysis
    metrics_data = {}
    if therapist._turns:
        last_turn = therapist._turns[-1]
        metrics_data = last_turn.get('metrics', {})

    return {
        "response": response,
        "state": current_state,
        "dialectic": dial,
        "metrics": metrics_data,
    }


def _generate_dream_response(engine, text: str, state: SessionState, analysis: Dict) -> str:
    """Generate dream exploration response.

    Uses DreamEngine for symbol extraction but still maintains
    therapeutic frame through context-aware prompting.
    """
    # Build context with dream and symbols
    dream_context = ""
    if state.dream_text:
        dream_context = f"\n\nTHE DREAM:\n{state.dream_text}\n"

    symbols_context = ""
    if state.symbols:
        symbols_context = f"\nSymbols: {', '.join([s.get('text', '') for s in state.symbols[:10]])}"
        # Add archetype info if available
        archetypes = [s.get('archetype', '') for s in state.symbols if s.get('archetype')]
        if archetypes:
            symbols_context += f"\nArchetypes present: {', '.join(set(archetypes))}"

    # Include semantic position
    position_context = f"\nSemantic position: A={state.A:+.2f}, S={state.S:+.2f}, tau={state.tau:.2f}"

    # History context
    history_context = ""
    if state.history:
        recent = state.history[-3:]
        history_context = "\n".join([
            f"Turn {h.get('turn', '?')}: User: {h.get('user', '')[:100]}..."
            for h in recent
        ])

    system = f"""You are a depth psychologist exploring a dream using Jungian analysis.
{dream_context}{symbols_context}{position_context}

Your approach:
1. Connect symbols to archetypal meanings (shadow, anima/animus, self, mother, father, hero, trickster)
2. Ask about emotional resonance - what feelings arise?
3. Explore personal associations to universal patterns
4. Keep responses focused and concise (2-4 sentences)
5. NEVER ask the user to repeat the dream

{f"Recent conversation:{chr(10)}{history_context}" if history_context else ""}"""

    prompt = f"""User says: "{text}"

Respond with depth psychological insight. Focus on one aspect at a time."""

    return engine._call_llm(system, prompt, max_tokens=300)


def _extract_archetypes(engine, state: SessionState) -> List[Dict[str, Any]]:
    """Extract archetypes from session using LLM analysis."""
    if not state.history:
        return []

    all_text = " ".join([
        h.get("user", "") + " " + h.get("therapist", "")
        for h in state.history
    ])

    system = """Analyze this session and identify Jungian archetypes that manifested.
Return JSON array:
[{"archetype": "shadow|anima_animus|self|mother|father|hero|trickster|death_rebirth",
  "symbols": ["symbol1"], "emotions": ["emotion1"], "context": "brief description"}]
Only include clearly present archetypes. Return [] if none."""

    symbol_text = f"\nSymbols: {', '.join([s.get('text', '') for s in state.symbols[:10]])}" if state.symbols else ""

    prompt = f"""Session content:
{all_text[:2500]}
{symbol_text}

Extract archetypes. Return only valid JSON array."""

    try:
        response = engine._call_llm(system, prompt, max_tokens=400)
        if "[" in response:
            json_str = response[response.index("["):response.rindex("]")+1]
            return json.loads(json_str)
    except (json.JSONDecodeError, ValueError, AttributeError):
        pass

    return []


@router.post("/start", response_model=SessionResponse)
async def start_session(
    data: SessionStart = None,
    current_user: Optional[Dict[str, Any]] = Depends(get_optional_user)
):
    """Start a new therapy/dream session."""
    user_id = current_user["user_id"] if current_user else None

    # Check for existing session
    if user_id:
        existing = get_user_active_session(user_id)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"You have an active session: {existing}. End it first."
            )

    # Create session
    session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    if user_id:
        session_id = f"{user_id[:8]}_{session_id}"

    mode = data.mode.value if data and data.mode else "hybrid"

    # Reset therapist state for new session
    therapist = get_therapist()
    therapist.reset()

    state = SessionState(
        session_id=session_id,
        user_id=user_id,
        mode=mode,
        started_at=datetime.now().isoformat(),
    )
    store_session(session_id, state)

    # Welcome message
    if mode == "dream":
        welcome = "Welcome to dream exploration. Share a dream you'd like to understand."
    elif mode == "therapy":
        welcome = "I'm here to listen. What's on your mind today?"
    else:
        welcome = "Welcome. You can share a dream, talk about what's weighing on you, or start wherever feels right."

    return SessionResponse(
        session_id=session_id,
        mode=SessionMode(mode),
        turn=0,
        response=welcome,
        symbols=[],
        emotions=[],
        themes=[],
    )


@router.post("/{session_id}/message", response_model=SessionResponse)
async def send_message(
    session_id: str,
    data: SessionMessage,
    current_user: Optional[Dict[str, Any]] = Depends(get_optional_user)
):
    """Send a message in the session.

    Uses the full Storm-Logos theoretical framework:
    - Therapy mode: Uses Therapist with MetricsEngine + Dialectic + RC-dynamics
    - Dream mode: Uses DreamEngine for symbol extraction + therapeutic framing
    """
    state = get_session(session_id)
    if not state:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )

    # Security: Verify ownership for user-owned sessions
    if state.user_id:
        # Session belongs to a user - require authentication
        if not current_user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required to access this session"
            )
        if state.user_id != current_user["user_id"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="This is not your session"
            )

    user_input = data.message.strip()

    # Get mode from request if provided, otherwise use session mode
    requested_mode = getattr(data, 'mode', None)
    if requested_mode and requested_mode != "auto":
        state.mode = requested_mode

    # Get engines
    dream_engine = get_dream_engine()
    therapist = get_therapist()

    # Analyze input for mode detection
    analysis = _analyze_input_mode(dream_engine, user_input, state.mode)

    # Check for goodbye
    if analysis.get("type") == "goodbye":
        return await end_session(session_id, current_user)

    # Update mode if hybrid and we can determine it
    if state.mode == "hybrid":
        if analysis.get("contains_dream") or analysis.get("mode_hint") == "dream":
            state.mode = "dream"
        elif analysis.get("mode_hint") == "therapy":
            state.mode = "therapy"

    # Extract symbols if dream content detected
    if analysis.get("contains_dream") or analysis.get("type") == "dream_content":
        if not state.dream_text:
            state.dream_text = user_input
        new_symbols = dream_engine.extract_symbols(user_input)
        for s in new_symbols:
            state.symbols.append({
                "text": s.raw_text,
                "archetype": s.archetype,
                "interpretation": s.interpretation,
                "A": s.bond.A,
                "S": s.bond.S,
                "tau": s.bond.tau,
            })

    # Track emotions and themes
    if analysis.get("emotions_detected"):
        state.emotions.extend(analysis["emotions_detected"])
    if analysis.get("key_symbols"):
        state.themes.extend(analysis["key_symbols"])

    # Generate response based on mode
    response_text = ""
    dialectic_info = {}

    if state.mode == "therapy" or (state.mode == "hybrid" and not analysis.get("contains_dream")):
        # Use full Therapist pipeline with theory
        result = _generate_therapy_response(therapist, user_input, state)
        response_text = result["response"]

        # Update semantic state from therapist's analysis
        if result.get("state"):
            semantic_state = result["state"]
            state.A = semantic_state.A
            state.S = semantic_state.S
            state.tau = semantic_state.tau
            state.irony = semantic_state.irony

        # Store dialectic analysis
        if result.get("dialectic"):
            dial = result["dialectic"]
            state.thesis_description = dial.get("thesis", {}).get("description", "")
            state.antithesis_description = dial.get("antithesis", {}).get("description", "")
            intervention = dial.get("intervention", {})
            state.intervention_direction = intervention.get("direction", "")
            dialectic_info = dial

        # Store defenses from metrics
        if result.get("metrics", {}).get("defenses"):
            state.defenses = result["metrics"]["defenses"]

    else:
        # Dream mode - use DreamEngine with therapeutic framing
        response_text = _generate_dream_response(dream_engine, user_input, state, analysis)

        # Still update coordinates from symbols if available
        if state.symbols:
            recent_symbols = state.symbols[-5:]
            state.A = sum(s.get("A", 0) for s in recent_symbols) / len(recent_symbols)
            state.S = sum(s.get("S", 0) for s in recent_symbols) / len(recent_symbols)
            state.tau = sum(s.get("tau", 2.5) for s in recent_symbols) / len(recent_symbols)

    # Update state
    state.turn += 1
    state.history.append({
        "turn": state.turn,
        "user": user_input,
        "therapist": response_text,
        "timestamp": datetime.now().isoformat(),
        "mode": state.mode,
        "semantic_state": {
            "A": state.A,
            "S": state.S,
            "tau": state.tau,
            "irony": state.irony,
        },
        "dialectic": dialectic_info if dialectic_info else None,
    })

    store_session(session_id, state)

    return SessionResponse(
        session_id=session_id,
        mode=SessionMode(state.mode),
        turn=state.turn,
        response=response_text,
        symbols=state.symbols[-5:],
        emotions=list(set(state.emotions[-5:])),
        themes=list(set(state.themes[-5:])),
    )


@router.post("/{session_id}/end", response_model=SessionEnd)
async def end_session(
    session_id: str,
    current_user: Optional[Dict[str, Any]] = Depends(get_optional_user)
):
    """End a session and extract archetypes."""
    state = get_session(session_id)
    if not state:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )

    # Security: Verify ownership for user-owned sessions
    if state.user_id:
        # Session belongs to a user - require authentication
        if not current_user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required to end this session"
            )
        if state.user_id != current_user["user_id"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="This is not your session"
            )

    # Once security checks pass, ensure session cleanup happens no matter what
    archetypes: List[Dict[str, Any]] = []
    try:
        engine = get_dream_engine()
        therapist = get_therapist()

        # Extract archetypes (optional - don't fail if this errors)
        try:
            archetypes = _extract_archetypes(engine, state)
        except Exception as e:
            logger.warning(f"Could not extract archetypes: {e}")

        # Get session summary from therapist if available
        try:
            session_data = therapist.get_session_data()
        except Exception as e:
            logger.warning(f"Could not get session data: {e}")

        # Save to user graph if authenticated (optional - don't fail if this errors)
        if state.user_id:
            try:
                manifestations = [
                    AM(
                        archetype=a.get("archetype", "unknown"),
                        symbols=a.get("symbols", []),
                        emotions=a.get("emotions", []),
                        context=a.get("context", ""),
                    )
                    for a in archetypes
                ]

                record = SessionRecord(
                    session_id=session_id,
                    user_id=state.user_id,
                    mode=state.mode,
                    timestamp=state.started_at,
                    dream_text=state.dream_text,
                    archetypes=manifestations,
                    symbols=[s.get("text", "") for s in state.symbols],
                    emotions=list(set(state.emotions)),
                    themes=list(set(state.themes)),
                    summary=f"{state.turn} turns, A={state.A:+.2f}, S={state.S:+.2f}",
                )

                ug = get_user_graph()
                ug.save_session(record)
            except Exception as e:
                logger.warning(f"Could not save to user graph: {e}")

    finally:
        # ALWAYS clean up session state, even if errors occurred above
        try:
            therapist = get_therapist()
            therapist.reset()
        except Exception:
            pass

        # ALWAYS remove from active sessions
        remove_session(session_id)

    return SessionEnd(
        session_id=session_id,
        turns=state.turn,
        mode=state.mode,
        symbols=state.symbols,
        emotions=list(set(state.emotions)),
        themes=list(set(state.themes)),
        archetypes=archetypes,
        summary=f"Session completed. {state.turn} turns, {len(state.symbols)} symbols, {len(archetypes)} archetypes. Final position: A={state.A:+.2f}, S={state.S:+.2f}, tau={state.tau:.2f}",
    )


@router.get("/{session_id}", response_model=SessionResponse)
async def get_session_state(
    session_id: str,
    current_user: Optional[Dict[str, Any]] = Depends(get_optional_user)
):
    """Get current session state."""
    state = get_session(session_id)
    if not state:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )

    # Security: Verify ownership for user-owned sessions
    if state.user_id:
        # Session belongs to a user - require authentication
        if not current_user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required to access this session"
            )
        if state.user_id != current_user["user_id"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="This is not your session"
            )

    return SessionResponse(
        session_id=session_id,
        mode=SessionMode(state.mode),
        turn=state.turn,
        response="",
        symbols=state.symbols[-10:],
        emotions=list(set(state.emotions[-10:])),
        themes=list(set(state.themes[-10:])),
    )


@router.delete("/{session_id}")
async def delete_session(
    session_id: str,
    current_user: Optional[Dict[str, Any]] = Depends(get_optional_user)
):
    """Delete a session without saving (discard)."""
    state = get_session(session_id)
    if not state:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )

    # Security: Verify ownership for user-owned sessions
    if state.user_id:
        # Session belongs to a user - require authentication
        if not current_user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required to delete this session"
            )
        if state.user_id != current_user["user_id"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="This is not your session"
            )

    # Once security checks pass, ensure cleanup happens no matter what
    try:
        therapist = get_therapist()
        therapist.reset()
    except Exception:
        pass
    finally:
        # ALWAYS remove from active sessions
        remove_session(session_id)

    return {"message": "Session deleted", "session_id": session_id}


@router.post("/{session_id}/pause")
async def pause_session(
    session_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Pause a session (save to Neo4j without ending)."""
    state = get_session(session_id)
    if not state:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )

    if state.user_id != current_user["user_id"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This is not your session"
        )

    # Once security checks pass, ensure cleanup happens no matter what
    try:
        # Save to Neo4j with paused status (optional - don't fail if this errors)
        try:
            # Convert symbols to the right format
            symbols_list = [s.get("text", "") if isinstance(s, dict) else s for s in state.symbols]

            record = SessionRecord(
                session_id=session_id,
                user_id=state.user_id,
                mode=state.mode,
                timestamp=state.started_at,
                dream_text=state.dream_text,
                archetypes=[],
                symbols=symbols_list,
                emotions=list(set(state.emotions)),
                themes=list(set(state.themes)),
                history=state.history,
                summary=f"{state.turn} turns (paused), A={state.A:+.2f}, S={state.S:+.2f}",
                status="paused",
            )

            ug = get_user_graph()
            ug.save_session(record)
        except Exception as e:
            logger.warning(f"Could not save session: {e}")

    finally:
        # ALWAYS clean up session state, even if errors occurred above
        try:
            therapist = get_therapist()
            therapist.reset()
        except Exception:
            pass

        # ALWAYS remove from active sessions
        remove_session(session_id)

    return {"message": "Session paused", "session_id": session_id, "turns": state.turn}


@router.post("/{session_id}/resume", response_model=SessionResponse)
async def resume_session(
    session_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Resume a paused session."""
    # Check if already active
    existing = get_session(session_id)
    if existing:
        return SessionResponse(
            session_id=session_id,
            mode=SessionMode(existing.mode),
            turn=existing.turn,
            response="Session already active.",
            symbols=existing.symbols[-5:],
            emotions=list(set(existing.emotions[-5:])),
            themes=list(set(existing.themes[-5:])),
        )

    # Load from Neo4j
    ug = get_user_graph()
    data = ug.load_session(session_id, current_user["user_id"])

    if not data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )

    # Convert symbols back to dict format
    symbols = []
    for s in data.get("symbols", []):
        if isinstance(s, str):
            symbols.append({"text": s, "archetype": None, "A": 0, "S": 0, "tau": 2.5})
        else:
            symbols.append(s)

    # Reconstruct session state
    state = SessionState(
        session_id=session_id,
        user_id=current_user["user_id"],
        mode=data.get("mode", "hybrid"),
        turn=len(data.get("history", [])),
        dream_text=data.get("dream_text"),
        symbols=symbols,
        themes=data.get("themes", []),
        emotions=data.get("emotions", []),
        history=data.get("history", []),
        started_at=data.get("timestamp", datetime.now().isoformat()),
    )

    # Restore semantic state from last history entry if available
    if state.history:
        last_entry = state.history[-1]
        semantic = last_entry.get("semantic_state", {})
        state.A = semantic.get("A", 0)
        state.S = semantic.get("S", 0)
        state.tau = semantic.get("tau", 2.5)
        state.irony = semantic.get("irony", 0)

    store_session(session_id, state)

    # Reset therapist for resumed session
    therapist = get_therapist()
    therapist.reset()

    # Update status in Neo4j
    ug.update_session_status(session_id, "active")

    return SessionResponse(
        session_id=session_id,
        mode=SessionMode(state.mode),
        turn=state.turn,
        response=f"Session resumed. We were at turn {state.turn}. Continue where we left off.",
        symbols=state.symbols[-5:],
        emotions=list(set(state.emotions[-5:])),
        themes=list(set(state.themes[-5:])),
    )
