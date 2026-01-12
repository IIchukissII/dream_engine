"""User Graph: Neo4j schema for user archetype evolution.

Tracks per-user, per-session archetype manifestations as symbols and emotions.
No numeric scores - archetypes are qualitative patterns.

Schema:
    (User)-[:SESSION]->(Session)
    (Session)-[:DREAM]->(Dream)
    (Session)-[:ARCHETYPE]->(ArchetypeManifestation)
    (ArchetypeManifestation)-[:SYMBOL]->(Symbol)
    (ArchetypeManifestation)-[:EMOTION]->(Emotion)
    (Dream)-[:CONTAINS]->(Symbol)
"""

import hashlib
import secrets
from datetime import datetime
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, field

import bcrypt

from .neo4j import get_neo4j


@dataclass
class User:
    """User model for therapy sessions."""
    username: str
    user_id: Optional[str] = None
    email: Optional[str] = None
    email_verified: bool = False
    display_name: Optional[str] = None
    avatar_url: Optional[str] = None
    created_at: Optional[str] = None
    password_hash: Optional[str] = None

    def __post_init__(self):
        if not self.user_id:
            self.user_id = self._generate_id()
        if not self.created_at:
            self.created_at = datetime.now().isoformat()

    def _generate_id(self) -> str:
        return hashlib.sha256(
            f"{self.username}:{secrets.token_hex(8)}".encode()
        ).hexdigest()[:16]

    @staticmethod
    def generate_token() -> str:
        """Generate a secure random token for email verification/password reset."""
        return secrets.token_urlsafe(32)

    def set_password(self, password: str):
        """Hash and store password using bcrypt."""
        self.password_hash = bcrypt.hashpw(
            password.encode(), bcrypt.gensalt(rounds=12)
        ).decode()

    def verify_password(self, password: str) -> bool:
        """Verify password against stored hash.

        Supports both bcrypt (new) and legacy SHA256 formats.
        Legacy passwords are auto-migrated to bcrypt on successful verification.
        """
        if not self.password_hash:
            return False

        # Check if bcrypt format ($2b$...)
        if self.password_hash.startswith('$2'):
            return bcrypt.checkpw(password.encode(), self.password_hash.encode())

        # Legacy SHA256 format (salt:hash)
        if ':' in self.password_hash:
            salt, stored_hash = self.password_hash.split(":", 1)
            check_hash = hashlib.sha256(f"{salt}:{password}".encode()).hexdigest()
            if check_hash == stored_hash:
                # Auto-migrate to bcrypt
                self.set_password(password)
                self._needs_hash_update = True
                return True

        return False

    @property
    def needs_hash_update(self) -> bool:
        """Check if password hash was migrated and needs DB update."""
        return getattr(self, '_needs_hash_update', False)


@dataclass
class ArchetypeManifestation:
    """How an archetype manifested in a session - through symbols and emotions."""
    archetype: str  # shadow, anima_animus, self, mother, father, hero, trickster, death_rebirth
    symbols: List[str] = field(default_factory=list)
    emotions: List[str] = field(default_factory=list)
    context: str = ""  # Brief description of how it appeared

    def as_dict(self) -> Dict:
        return {
            "archetype": self.archetype,
            "symbols": self.symbols,
            "emotions": self.emotions,
            "context": self.context,
        }


@dataclass
class BookConcept:
    """A concept from corpus (Jung, Freud, etc.) that resonated."""
    source: str  # jung, freud, etc.
    concept: str  # The concept/quote
    context: str = ""  # How it relates to session
    similarity: float = 0.0  # Semantic similarity

    def as_dict(self) -> Dict:
        return {
            "source": self.source,
            "concept": self.concept,
            "context": self.context,
            "similarity": self.similarity,
        }


@dataclass
class SessionRecord:
    """Record of a therapy/dream session."""
    session_id: str
    user_id: str
    mode: str  # dream, therapy, hybrid
    timestamp: str
    dream_text: Optional[str] = None
    archetypes: List[ArchetypeManifestation] = field(default_factory=list)
    symbols: List[str] = field(default_factory=list)
    emotions: List[str] = field(default_factory=list)
    themes: List[str] = field(default_factory=list)
    concepts: List[BookConcept] = field(default_factory=list)  # Book concepts
    history: List[Dict] = field(default_factory=list)  # Conversation history
    summary: str = ""
    status: str = "ended"  # active, paused, ended

    def as_dict(self) -> Dict:
        return {
            "session_id": self.session_id,
            "user_id": self.user_id,
            "mode": self.mode,
            "timestamp": self.timestamp,
            "dream_text": self.dream_text,
            "archetypes": [a.as_dict() for a in self.archetypes],
            "symbols": self.symbols,
            "emotions": self.emotions,
            "themes": self.themes,
            "concepts": [c.as_dict() for c in self.concepts],
            "history": self.history,
            "summary": self.summary,
            "status": self.status,
        }


class UserGraph:
    """Neo4j interface for user archetype evolution tracking."""

    def __init__(self):
        self._neo4j = get_neo4j()
        self._connected = False

    def connect(self) -> bool:
        """Connect to Neo4j."""
        if self._neo4j.connect():
            self._connected = True
            self._ensure_constraints()
            return True
        return False

    def _ensure_constraints(self):
        """Create indexes and constraints."""
        queries = [
            "CREATE CONSTRAINT user_id IF NOT EXISTS FOR (u:User) REQUIRE u.user_id IS UNIQUE",
            "CREATE CONSTRAINT username IF NOT EXISTS FOR (u:User) REQUIRE u.username IS UNIQUE",
            "CREATE INDEX session_timestamp IF NOT EXISTS FOR (s:TherapySession) ON (s.timestamp)",
            "CREATE INDEX archetype_name IF NOT EXISTS FOR (a:Archetype) ON (a.name)",
        ]
        with self._neo4j._driver.session() as session:
            for q in queries:
                try:
                    session.run(q)
                except Exception:
                    pass  # Constraint may already exist

    # =========================================================================
    # USER MANAGEMENT
    # =========================================================================

    def create_user(self, username: str, password: str, email: str = None) -> Optional[User]:
        """Create a new user."""
        user = User(username=username, email=email)
        user.set_password(password)

        query = """
        CREATE (u:User {
            user_id: $user_id,
            username: $username,
            email: $email,
            email_verified: false,
            password_hash: $password_hash,
            created_at: $created_at
        })
        RETURN u
        """
        try:
            with self._neo4j._driver.session() as session:
                session.run(query,
                    user_id=user.user_id,
                    username=user.username,
                    email=user.email,
                    password_hash=user.password_hash,
                    created_at=user.created_at
                )
            return user
        except Exception as e:
            print(f"Error creating user: {e}")
            return None

    def get_user(self, username: str) -> Optional[User]:
        """Get user by username."""
        query = """
        MATCH (u:User {username: $username})
        RETURN u.user_id as user_id, u.username as username,
               u.email as email, u.email_verified as email_verified,
               u.display_name as display_name, u.avatar_url as avatar_url,
               u.password_hash as password_hash, u.created_at as created_at
        """
        with self._neo4j._driver.session() as session:
            result = session.run(query, username=username)
            record = result.single()
            if record:
                return User(
                    user_id=record["user_id"],
                    username=record["username"],
                    email=record["email"],
                    email_verified=record["email_verified"] or False,
                    display_name=record["display_name"],
                    avatar_url=record["avatar_url"],
                    password_hash=record["password_hash"],
                    created_at=record["created_at"]
                )
        return None

    def get_user_by_email(self, email: str) -> Optional[User]:
        """Get user by email address."""
        query = """
        MATCH (u:User {email: $email})
        RETURN u.user_id as user_id, u.username as username,
               u.email as email, u.email_verified as email_verified,
               u.display_name as display_name, u.avatar_url as avatar_url,
               u.password_hash as password_hash, u.created_at as created_at
        """
        with self._neo4j._driver.session() as session:
            result = session.run(query, email=email)
            record = result.single()
            if record:
                return User(
                    user_id=record["user_id"],
                    username=record["username"],
                    email=record["email"],
                    email_verified=record["email_verified"] or False,
                    display_name=record["display_name"],
                    avatar_url=record["avatar_url"],
                    password_hash=record["password_hash"],
                    created_at=record["created_at"]
                )
        return None

    def get_user_by_id(self, user_id: str) -> Optional[User]:
        """Get user by user_id."""
        query = """
        MATCH (u:User {user_id: $user_id})
        RETURN u.user_id as user_id, u.username as username,
               u.email as email, u.email_verified as email_verified,
               u.display_name as display_name, u.avatar_url as avatar_url,
               u.password_hash as password_hash, u.created_at as created_at
        """
        with self._neo4j._driver.session() as session:
            result = session.run(query, user_id=user_id)
            record = result.single()
            if record:
                return User(
                    user_id=record["user_id"],
                    username=record["username"],
                    email=record["email"],
                    email_verified=record["email_verified"] or False,
                    display_name=record["display_name"],
                    avatar_url=record["avatar_url"],
                    password_hash=record["password_hash"],
                    created_at=record["created_at"]
                )
        return None

    def verify_email(self, user_id: str) -> bool:
        """Mark user's email as verified."""
        query = """
        MATCH (u:User {user_id: $user_id})
        SET u.email_verified = true
        RETURN u
        """
        try:
            with self._neo4j._driver.session() as session:
                result = session.run(query, user_id=user_id)
                return result.single() is not None
        except Exception as e:
            print(f"Error verifying email: {e}")
            return False

    def update_profile(self, user_id: str, display_name: str = None, avatar_url: str = None) -> bool:
        """Update user profile fields."""
        updates = []
        params = {"user_id": user_id}

        if display_name is not None:
            updates.append("u.display_name = $display_name")
            params["display_name"] = display_name
        if avatar_url is not None:
            updates.append("u.avatar_url = $avatar_url")
            params["avatar_url"] = avatar_url

        if not updates:
            return True

        query = f"""
        MATCH (u:User {{user_id: $user_id}})
        SET {', '.join(updates)}
        RETURN u
        """
        try:
            with self._neo4j._driver.session() as session:
                result = session.run(query, **params)
                return result.single() is not None
        except Exception as e:
            print(f"Error updating profile: {e}")
            return False

    def authenticate(self, username: str, password: str) -> Optional[User]:
        """Authenticate user and return User if valid.

        Auto-migrates legacy SHA256 passwords to bcrypt on successful login.
        """
        user = self.get_user(username)
        if user and user.verify_password(password):
            # Auto-migrate password hash if needed
            if user.needs_hash_update:
                self._update_password_hash(user.user_id, user.password_hash)
            return user
        return None

    def _update_password_hash(self, user_id: str, new_hash: str) -> bool:
        """Update user's password hash in Neo4j."""
        query = """
        MATCH (u:User {user_id: $user_id})
        SET u.password_hash = $password_hash
        RETURN u
        """
        try:
            with self._neo4j._driver.session() as session:
                session.run(query, user_id=user_id, password_hash=new_hash)
            return True
        except Exception as e:
            print(f"Error updating password hash: {e}")
            return False

    def update_password(self, user_id: str, new_password: str) -> bool:
        """Update user's password (for password change/reset)."""
        new_hash = bcrypt.hashpw(
            new_password.encode(), bcrypt.gensalt(rounds=12)
        ).decode()
        return self._update_password_hash(user_id, new_hash)

    # =========================================================================
    # SESSION STORAGE
    # =========================================================================

    def save_session(self, record: SessionRecord) -> bool:
        """Save a therapy session with archetype manifestations."""
        import json

        # Create session node
        session_query = """
        MATCH (u:User {user_id: $user_id})
        MERGE (s:TherapySession {session_id: $session_id})
        SET s.mode = $mode,
            s.timestamp = $timestamp,
            s.dream_text = $dream_text,
            s.summary = $summary,
            s.history = $history,
            s.status = $status,
            s.symbols_json = $symbols_json,
            s.emotions_json = $emotions_json,
            s.themes_json = $themes_json
        MERGE (u)-[:SESSION]->(s)
        RETURN s
        """

        with self._neo4j._driver.session() as session:
            # Create/update session
            session.run(session_query,
                user_id=record.user_id,
                session_id=record.session_id,
                mode=record.mode,
                timestamp=record.timestamp,
                dream_text=record.dream_text or "",
                summary=record.summary,
                history=json.dumps(record.history),
                status=record.status,
                symbols_json=json.dumps(record.symbols),
                emotions_json=json.dumps(record.emotions),
                themes_json=json.dumps(record.themes),
            )

            # Create archetype manifestations
            for arch in record.archetypes:
                self._save_archetype_manifestation(session, record.session_id, arch)

            # Link symbols to session
            for symbol in record.symbols:
                self._link_symbol(session, record.session_id, symbol)

            # Link emotions to session
            for emotion in record.emotions:
                self._link_emotion(session, record.session_id, emotion)

            # Link book concepts to session
            for concept in record.concepts:
                self._link_concept(session, record.session_id, concept)

        return True

    def _save_archetype_manifestation(self, session, session_id: str,
                                       manifestation: ArchetypeManifestation):
        """Save an archetype manifestation with its symbols and emotions."""
        # Create or merge archetype node
        arch_query = """
        MATCH (s:TherapySession {session_id: $session_id})
        MERGE (a:Archetype {name: $archetype})
        CREATE (m:ArchetypeManifestation {
            context: $context,
            timestamp: datetime()
        })
        CREATE (s)-[:MANIFESTED]->(m)
        CREATE (m)-[:OF_ARCHETYPE]->(a)
        RETURN m
        """
        session.run(arch_query,
            session_id=session_id,
            archetype=manifestation.archetype,
            context=manifestation.context
        )

        # Link symbols to manifestation
        for symbol in manifestation.symbols:
            symbol_query = """
            MATCH (s:TherapySession {session_id: $session_id})
            MATCH (s)-[:MANIFESTED]->(m:ArchetypeManifestation)-[:OF_ARCHETYPE]->(a:Archetype {name: $archetype})
            MERGE (sym:Symbol {text: $symbol})
            MERGE (m)-[:THROUGH_SYMBOL]->(sym)
            """
            session.run(symbol_query,
                session_id=session_id,
                archetype=manifestation.archetype,
                symbol=symbol
            )

        # Link emotions to manifestation
        for emotion in manifestation.emotions:
            emotion_query = """
            MATCH (s:TherapySession {session_id: $session_id})
            MATCH (s)-[:MANIFESTED]->(m:ArchetypeManifestation)-[:OF_ARCHETYPE]->(a:Archetype {name: $archetype})
            MERGE (e:Emotion {name: $emotion})
            MERGE (m)-[:FELT_AS]->(e)
            """
            session.run(emotion_query,
                session_id=session_id,
                archetype=manifestation.archetype,
                emotion=emotion
            )

    def _link_symbol(self, session, session_id: str, symbol: str):
        """Link a symbol to a session."""
        query = """
        MATCH (s:TherapySession {session_id: $session_id})
        MERGE (sym:Symbol {text: $symbol})
        MERGE (s)-[:CONTAINS_SYMBOL]->(sym)
        """
        session.run(query, session_id=session_id, symbol=symbol)

    def _link_emotion(self, session, session_id: str, emotion: str):
        """Link an emotion to a session."""
        query = """
        MATCH (s:TherapySession {session_id: $session_id})
        MERGE (e:Emotion {name: $emotion})
        MERGE (s)-[:FELT]->(e)
        """
        session.run(query, session_id=session_id, emotion=emotion)

    def _link_concept(self, session, session_id: str, concept: BookConcept):
        """Link a book concept to a session."""
        query = """
        MATCH (s:TherapySession {session_id: $session_id})
        MERGE (src:CorpusSource {name: $source})
        MERGE (c:BookConcept {text: $concept})
        MERGE (c)-[:FROM_SOURCE]->(src)
        CREATE (r:ConceptResonance {
            context: $context,
            similarity: $similarity,
            timestamp: datetime()
        })
        CREATE (s)-[:RESONATED]->(r)
        CREATE (r)-[:WITH_CONCEPT]->(c)
        """
        session.run(query,
            session_id=session_id,
            source=concept.source,
            concept=concept.concept,
            context=concept.context,
            similarity=concept.similarity
        )

    # =========================================================================
    # EVOLUTION QUERIES
    # =========================================================================

    def get_user_sessions(self, user_id: str, limit: int = 20) -> List[Dict]:
        """Get user's session history."""
        query = """
        MATCH (u:User {user_id: $user_id})-[:SESSION]->(s:TherapySession)
        OPTIONAL MATCH (s)-[:MANIFESTED]->(m)-[:OF_ARCHETYPE]->(a:Archetype)
        WITH s, collect(DISTINCT a.name) as archetypes
        RETURN s.session_id as session_id, s.mode as mode,
               s.timestamp as timestamp, s.summary as summary,
               s.status as status, archetypes
        ORDER BY s.timestamp DESC
        LIMIT $limit
        """
        results = []
        with self._neo4j._driver.session() as session:
            records = session.run(query, user_id=user_id, limit=limit)
            for r in records:
                results.append({
                    "session_id": r["session_id"],
                    "mode": r["mode"],
                    "timestamp": r["timestamp"],
                    "summary": r["summary"],
                    "status": r["status"] or "ended",
                    "archetypes": r["archetypes"],
                })
        return results

    def load_session(self, session_id: str, user_id: str) -> Optional[Dict]:
        """Load full session data for resuming."""
        import json

        query = """
        MATCH (u:User {user_id: $user_id})-[:SESSION]->(s:TherapySession {session_id: $session_id})
        RETURN s.session_id as session_id, s.mode as mode,
               s.timestamp as timestamp, s.dream_text as dream_text,
               s.summary as summary, s.history as history,
               s.status as status, s.symbols_json as symbols_json,
               s.emotions_json as emotions_json, s.themes_json as themes_json
        """
        with self._neo4j._driver.session() as session:
            result = session.run(query, session_id=session_id, user_id=user_id)
            record = result.single()
            if record:
                return {
                    "session_id": record["session_id"],
                    "user_id": user_id,
                    "mode": record["mode"],
                    "timestamp": record["timestamp"],
                    "dream_text": record["dream_text"],
                    "summary": record["summary"],
                    "history": json.loads(record["history"] or "[]"),
                    "status": record["status"] or "ended",
                    "symbols": json.loads(record["symbols_json"] or "[]"),
                    "emotions": json.loads(record["emotions_json"] or "[]"),
                    "themes": json.loads(record["themes_json"] or "[]"),
                }
        return None

    def update_session_status(self, session_id: str, status: str) -> bool:
        """Update session status (active, paused, ended)."""
        query = """
        MATCH (s:TherapySession {session_id: $session_id})
        SET s.status = $status
        RETURN s
        """
        with self._neo4j._driver.session() as session:
            result = session.run(query, session_id=session_id, status=status)
            return result.single() is not None

    def get_archetype_evolution(self, user_id: str, archetype: str) -> List[Dict]:
        """Get how a specific archetype has manifested over time."""
        query = """
        MATCH (u:User {user_id: $user_id})-[:SESSION]->(s:TherapySession)
        MATCH (s)-[:MANIFESTED]->(m)-[:OF_ARCHETYPE]->(a:Archetype {name: $archetype})
        OPTIONAL MATCH (m)-[:THROUGH_SYMBOL]->(sym:Symbol)
        OPTIONAL MATCH (m)-[:FELT_AS]->(e:Emotion)
        WITH s, m, collect(DISTINCT sym.text) as symbols, collect(DISTINCT e.name) as emotions
        RETURN s.session_id as session_id, s.timestamp as timestamp,
               m.context as context, symbols, emotions
        ORDER BY s.timestamp
        """
        results = []
        with self._neo4j._driver.session() as session:
            records = session.run(query, user_id=user_id, archetype=archetype)
            for r in records:
                results.append({
                    "session_id": r["session_id"],
                    "timestamp": r["timestamp"],
                    "context": r["context"],
                    "symbols": r["symbols"],
                    "emotions": r["emotions"],
                })
        return results

    def get_recurring_symbols(self, user_id: str, min_count: int = 2) -> List[Dict]:
        """Get symbols that recur across sessions."""
        query = """
        MATCH (u:User {user_id: $user_id})-[:SESSION]->(s:TherapySession)
        MATCH (s)-[:CONTAINS_SYMBOL]->(sym:Symbol)
        WITH sym.text as symbol, count(DISTINCT s) as occurrences,
             collect(DISTINCT s.timestamp) as sessions
        WHERE occurrences >= $min_count
        RETURN symbol, occurrences, sessions
        ORDER BY occurrences DESC
        """
        results = []
        with self._neo4j._driver.session() as session:
            records = session.run(query, user_id=user_id, min_count=min_count)
            for r in records:
                results.append({
                    "symbol": r["symbol"],
                    "occurrences": r["occurrences"],
                    "sessions": r["sessions"],
                })
        return results

    def get_archetype_symbols(self, user_id: str, archetype: str) -> List[Dict]:
        """Get all symbols through which an archetype has manifested for a user."""
        query = """
        MATCH (u:User {user_id: $user_id})-[:SESSION]->(s:TherapySession)
        MATCH (s)-[:MANIFESTED]->(m)-[:OF_ARCHETYPE]->(a:Archetype {name: $archetype})
        MATCH (m)-[:THROUGH_SYMBOL]->(sym:Symbol)
        WITH sym.text as symbol, count(*) as frequency
        RETURN symbol, frequency
        ORDER BY frequency DESC
        """
        results = []
        with self._neo4j._driver.session() as session:
            records = session.run(query, user_id=user_id, archetype=archetype)
            for r in records:
                results.append({
                    "symbol": r["symbol"],
                    "frequency": r["frequency"],
                })
        return results

    def get_concept_evolution(self, user_id: str, source: str = None) -> List[Dict]:
        """Get book concepts that have resonated over time."""
        if source:
            query = """
            MATCH (u:User {user_id: $user_id})-[:SESSION]->(s:TherapySession)
            MATCH (s)-[:RESONATED]->(r:ConceptResonance)-[:WITH_CONCEPT]->(c:BookConcept)
            MATCH (c)-[:FROM_SOURCE]->(src:CorpusSource {name: $source})
            RETURN s.session_id as session_id, s.timestamp as timestamp,
                   c.text as concept, r.context as context, r.similarity as similarity,
                   src.name as source
            ORDER BY s.timestamp
            """
            params = {"user_id": user_id, "source": source}
        else:
            query = """
            MATCH (u:User {user_id: $user_id})-[:SESSION]->(s:TherapySession)
            MATCH (s)-[:RESONATED]->(r:ConceptResonance)-[:WITH_CONCEPT]->(c:BookConcept)
            MATCH (c)-[:FROM_SOURCE]->(src:CorpusSource)
            RETURN s.session_id as session_id, s.timestamp as timestamp,
                   c.text as concept, r.context as context, r.similarity as similarity,
                   src.name as source
            ORDER BY s.timestamp
            """
            params = {"user_id": user_id}

        results = []
        with self._neo4j._driver.session() as session:
            records = session.run(query, **params)
            for r in records:
                results.append({
                    "session_id": r["session_id"],
                    "timestamp": r["timestamp"],
                    "concept": r["concept"],
                    "context": r["context"],
                    "similarity": r["similarity"],
                    "source": r["source"],
                })
        return results

    def get_recurring_concepts(self, user_id: str, min_count: int = 2) -> List[Dict]:
        """Get concepts that recur across sessions."""
        query = """
        MATCH (u:User {user_id: $user_id})-[:SESSION]->(s:TherapySession)
        MATCH (s)-[:RESONATED]->(r)-[:WITH_CONCEPT]->(c:BookConcept)
        MATCH (c)-[:FROM_SOURCE]->(src:CorpusSource)
        WITH c.text as concept, src.name as source, count(DISTINCT s) as occurrences
        WHERE occurrences >= $min_count
        RETURN concept, source, occurrences
        ORDER BY occurrences DESC
        """
        results = []
        with self._neo4j._driver.session() as session:
            records = session.run(query, user_id=user_id, min_count=min_count)
            for r in records:
                results.append({
                    "concept": r["concept"],
                    "source": r["source"],
                    "occurrences": r["occurrences"],
                })
        return results

    def get_emotional_patterns(self, user_id: str) -> Dict[str, List[str]]:
        """Get which emotions associate with which archetypes for a user."""
        query = """
        MATCH (u:User {user_id: $user_id})-[:SESSION]->(s:TherapySession)
        MATCH (s)-[:MANIFESTED]->(m)-[:OF_ARCHETYPE]->(a:Archetype)
        MATCH (m)-[:FELT_AS]->(e:Emotion)
        WITH a.name as archetype, e.name as emotion, count(*) as freq
        RETURN archetype, collect({emotion: emotion, freq: freq}) as emotions
        """
        results = {}
        with self._neo4j._driver.session() as session:
            records = session.run(query, user_id=user_id)
            for r in records:
                results[r["archetype"]] = [
                    e["emotion"] for e in sorted(r["emotions"], key=lambda x: -x["freq"])
                ]
        return results

    def get_all_users_stats(self) -> List[Dict[str, Any]]:
        """Get all users with their activity statistics. For admin dashboard."""
        query = """
        MATCH (u:User)
        OPTIONAL MATCH (u)-[:SESSION]->(s:TherapySession)
        OPTIONAL MATCH (u)-[:DREAMED]->(d:Dream)
        WITH u, count(DISTINCT s) as session_count, count(DISTINCT d) as dream_count
        RETURN u.user_id as user_id, u.username as username,
               u.email as email, u.email_verified as email_verified,
               u.display_name as display_name, u.created_at as created_at,
               session_count, dream_count
        ORDER BY u.created_at DESC
        """
        results = []
        with self._neo4j._driver.session() as session:
            records = session.run(query)
            for r in records:
                results.append({
                    "user_id": r["user_id"],
                    "username": r["username"],
                    "email": r["email"],
                    "email_verified": r["email_verified"] or False,
                    "display_name": r["display_name"],
                    "created_at": r["created_at"],
                    "session_count": r["session_count"],
                    "dream_count": r["dream_count"],
                    "total_activity": r["session_count"] + r["dream_count"],
                })
        return results

    def get_user_archetype_profile(self, user_id: str) -> Dict[str, Any]:
        """Get comprehensive archetype profile for a user."""
        query = """
        MATCH (u:User {user_id: $user_id})-[:SESSION]->(s:TherapySession)
        MATCH (s)-[:MANIFESTED]->(m)-[:OF_ARCHETYPE]->(a:Archetype)
        WITH a.name as archetype, count(DISTINCT s) as session_count
        RETURN archetype, session_count
        ORDER BY session_count DESC
        """

        profile = {
            "archetypes": {},
            "total_sessions": 0,
            "dominant_archetypes": [],
        }

        with self._neo4j._driver.session() as session:
            # Get archetype frequencies
            records = session.run(query, user_id=user_id)
            for r in records:
                profile["archetypes"][r["archetype"]] = r["session_count"]

            # Get total sessions
            count_query = """
            MATCH (u:User {user_id: $user_id})-[:SESSION]->(s:TherapySession)
            RETURN count(s) as total
            """
            result = session.run(count_query, user_id=user_id).single()
            if result:
                profile["total_sessions"] = result["total"]

        # Determine dominant archetypes (appear in >30% of sessions)
        if profile["total_sessions"] > 0:
            threshold = profile["total_sessions"] * 0.3
            profile["dominant_archetypes"] = [
                arch for arch, count in profile["archetypes"].items()
                if count >= threshold
            ]

        return profile


# Singleton
_user_graph: Optional[UserGraph] = None


def get_user_graph() -> UserGraph:
    """Get singleton UserGraph instance."""
    global _user_graph
    if _user_graph is None:
        _user_graph = UserGraph()
    return _user_graph
