# Storm-Logos Core Library

Technical reference for the 8-layer adaptive semantic generation system.

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│  LAYER 8: APPLICATIONS                                         │
│  therapist.py, generator.py, analyzer.py, navigator.py         │
├─────────────────────────────────────────────────────────────────┤
│  LAYER 7: ORCHESTRATION                                        │
│  orchestration/engine.py - Measure → Adapt → Generate loop     │
├─────────────────────────────────────────────────────────────────┤
│  LAYER 6: ADAPTIVE CONTROLLER                                  │
│  controller/pi_controller.py - PI control: Δp = η·error + κ·∫  │
├─────────────────────────────────────────────────────────────────┤
│  LAYER 5: GENERATION ENGINE                                    │
│  generation/pipeline.py - Storm → Dialectic → Chain            │
├─────────────────────────────────────────────────────────────────┤
│  LAYER 4: FEEDBACK ENGINE                                      │
│  feedback/engine.py - Error = target - current                 │
├─────────────────────────────────────────────────────────────────┤
│  LAYER 3: METRICS ENGINE                                       │
│  metrics/ - Extractors + Analyzers (coherence, irony, tau)     │
├─────────────────────────────────────────────────────────────────┤
│  LAYER 2: SEMANTIC LAYER                                       │
│  semantic/ - Storm, Dialectic, Chain, Physics, State           │
├─────────────────────────────────────────────────────────────────┤
│  LAYER 1: DATA LAYER                                           │
│  data/ - PostgreSQL (coordinates) + Neo4j (trajectories)       │
└─────────────────────────────────────────────────────────────────┘
```

## Module Structure

```
storm_logos/
├── applications/           # Layer 8: User-facing applications
│   ├── therapist.py           # Therapeutic AI agent
│   ├── analyzer.py            # Text/trajectory analysis
│   ├── generator.py           # Semantic text generation
│   ├── navigator.py           # Semantic space navigation
│   └── dream.py               # Dream analysis engine
├── data/                   # Layer 1: Data access
│   ├── postgres.py            # PostgreSQL client
│   ├── neo4j.py               # Neo4j graph client
│   ├── models.py              # Bond, Trajectory, SemanticState
│   ├── book_parser.py         # spaCy-based book parser
│   ├── bond_learner.py        # Runtime bond learning
│   ├── weight_dynamics.py     # Learning/forgetting formulas
│   ├── user_graph.py          # User evolution tracking
│   └── cache.py               # Redis caching
├── semantic/               # Layer 2: Semantic operations
│   ├── storm.py               # Candidate explosion
│   ├── dialectic.py           # Thesis-antithesis filtering
│   ├── chain.py               # Chain reaction selection
│   ├── physics.py             # RC dynamics, gravity
│   └── state.py               # SemanticState management
├── metrics/                # Layer 3: Metrics extraction
│   ├── engine.py              # MetricsEngine
│   ├── extractors/            # Text → bonds
│   └── analyzers/             # Coherence, irony, tension
├── feedback/               # Layer 4: Error computation
│   ├── engine.py              # FeedbackEngine
│   └── targets.py             # Homeostatic targets
├── generation/             # Layer 5: Generation pipeline
│   ├── engine.py              # GenerationEngine
│   └── pipeline.py            # Storm→Dialectic→Chain
├── controller/             # Layer 6: PI control
│   ├── engine.py              # AdaptiveController
│   └── pi_controller.py       # PI algorithm
├── orchestration/          # Layer 7: Main loop
│   ├── engine.py              # Orchestrator
│   └── loop.py                # Main control loop
├── services/               # Web services
│   ├── api/                   # FastAPI backend
│   └── frontend-react/        # React frontend
├── migrations/             # Database migrations
│   └── versions/              # Alembic migration files
├── scripts/                # Utility scripts
└── config/                 # Configuration files
```

## Core Concepts

### Semantic Space (A, S, τ)

Every word and concept maps to 3D coordinates:

| Axis | Name | Range | Description |
|------|------|-------|-------------|
| A | Affirmation | [-1, +1] | bad ↔ good (valence) |
| S | Sacred | [-1, +1] | mundane ↔ elevated |
| τ | Tau | [0, 5] | concrete ↔ abstract |

### Bond

A semantic unit combining adjective + noun:

```python
from storm_logos.data.models import Bond

bond = Bond(
    adj="dark",
    noun="forest",
    A=0.32,
    S=-0.01,
    tau=1.2
)
```

### Trajectory

Sequence of bonds representing semantic movement:

```python
from storm_logos.data.models import Trajectory

trajectory = Trajectory(bonds=[bond1, bond2, bond3])
print(trajectory.coherence)  # Inter-bond coherence
print(trajectory.tau_slope)  # Abstraction direction
```

## Python API

### Data Layer

```python
from storm_logos.data.postgres import get_data
from storm_logos.data.neo4j import get_neo4j

# PostgreSQL - word coordinates
data = get_data()
A, S, tau = data.get_word_coords("forest")
bond = data.get_bond("dark", "forest")

# Neo4j - trajectories
neo = get_neo4j()
neo.connect()
trajectory = neo.get_book_trajectory("jung_collected_papers", limit=100)
stats = neo.stats()
```

### Applications

```python
from storm_logos.applications.analyzer import Analyzer
from storm_logos.applications.therapist import Therapist

# Analyze text
analyzer = Analyzer()
result = analyzer.analyze_text("The dark forest held ancient secrets.")
print(f"Position: A={result['position']['A']:.2f}, S={result['position']['S']:.2f}")
print(f"Coherence: {result['coherence']:.2f}")

# Therapy session
therapist = Therapist(model="groq:llama-3.3-70b-versatile")
response = therapist.respond("I keep having this recurring dream...")
print(response.text)
print(f"Analysis: A={response.state.A:.2f}, irony={response.state.irony:.0%}")
```

### Dream Analysis

```python
from storm_logos.applications.dream import DreamAnalyzer

analyzer = DreamAnalyzer()
result = analyzer.analyze("""
    I was walking through a dark forest. An old woman
    with a lantern led me to a cave with a mirror inside.
""")

print("Symbols:", result.symbols)
print("Archetypes:", result.archetypes)
print("Corpus resonances:", result.resonances)
print("Interpretation:", result.interpretation)
```

### Bond Learning

```python
from storm_logos.data.bond_learner import BondLearner

learner = BondLearner()
learner.connect()

# Learn from text
result = learner.learn_from_text("The mysterious path led deeper into shadows.")
print(result.summary())  # "Learned 3 bonds: 2 new, 1 reinforced"

# Learn with conversation context
result = learner.learn_turn(
    text="The light revealed hidden truths.",
    conversation_id="conv_123",
    previous_bonds=result.bonds
)
```

### Weight Dynamics

```python
from storm_logos.data.weight_dynamics import decay_weight, time_to_dormancy

# Decay calculation (user edges only, corpus never decays)
w_after_week = decay_weight(1.0, days_elapsed=7)  # 0.763
days_to_dormant = time_to_dormancy(1.0)  # ~44 days

# Apply decay via Neo4j
from storm_logos.data.neo4j import get_neo4j
neo = get_neo4j()
neo.connect()
stats = neo.apply_decay(days_elapsed=1.0, dry_run=False)
```

## RC-Model Dynamics

### State Update Formula

```
dQ/dt = (x_w - Q) × (1 - |Q|/Q_max) - Q × decay
```

Where:
- Q = current state
- x_w = input from word/bond
- Q_max = saturation limit
- decay = natural decay rate

### Boltzmann Factor

Transition probability for abstraction jumps:

```
P(Δτ) ∝ exp(-|Δτ|/kT)  where kT ≈ 0.819
```

### Chain Reaction (Resonance)

```python
power = Σ coherence(candidate, history[i]) × decay^i
if power > threshold:
    power = threshold + (power - threshold)²  # Lasing effect
```

## Homeostatic Targets

| Metric | Target | Description |
|--------|--------|-------------|
| Coherence | 0.70 | Inter-bond semantic similarity |
| Irony | 0.15 | Saying opposite of meaning |
| Tension | 0.60 | Dialectic opposition |
| τ Variance | 0.80 | Abstraction level variation |
| Noise Ratio | 0.20 | Random vs structured |
| τ Slope | -0.10 | Drift toward concrete |

## Neo4j Schema

```cypher
// Nodes
(:Book {id, title, author, filename, genre})
(:Bond {id, adj, noun, A, S, tau, source})
(:User {user_id, username, password_hash})
(:TherapySession {session_id, mode, timestamp, status})

// Relationships
(:Book)-[:CONTAINS]->(Bond)
(:Bond)-[:FOLLOWS {book_id, weight, source}]->(:Bond)
(:User)-[:SESSION]->(:TherapySession)
```

## PostgreSQL Schema

```sql
-- Word coordinates (derived from corpus)
word_coordinates (word, A, S, tau)

-- Hypothetical bond vocabulary
hyp_bond_vocab (id, adj, noun, A, S, tau)

-- Learned bonds from conversations
learned_bonds (id, adj, noun, A, S, tau, source, confidence, use_count)

-- Users
users (id, username, password_hash, email, created_at)

-- Sessions
sessions (id, user_id, mode, status, created_at)
```

## Configuration

### Environment Variables

```bash
# LLM
GROQ_API_KEY=gsk_...
ANTHROPIC_API_KEY=sk-ant-...
LLM_MODEL=groq:llama-3.3-70b-versatile

# PostgreSQL
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=semantic
POSTGRES_USER=postgres
POSTGRES_PASSWORD=...

# Neo4j
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=...

# Redis
REDIS_URL=redis://localhost:6379/0

# API
JWT_SECRET=...
CORS_ORIGINS=http://localhost:3000
```

## Scripts

```bash
# Process books into Neo4j
python -m storm_logos.scripts.process_books --priority
python -m storm_logos.scripts.process_books --file /path/to/book.txt

# Apply forgetting decay (cron job)
python -m storm_logos.scripts.nightly_decay
python -m storm_logos.scripts.nightly_decay --days 7 --dry-run

# Sync learned bonds to Neo4j
python -m storm_logos.scripts.sync_bonds --all

# Dream analysis CLI
python -m storm_logos.scripts.dream_analysis --interactive
```

## Testing

```bash
# Run tests
pytest storm_logos/tests/

# Specific test modules
pytest storm_logos/tests/test_weight_dynamics.py
pytest storm_logos/tests/test_bond_learning.py
```

## Processed Corpus

### Books by Category

| Category | Books | Bonds | Key Authors |
|----------|-------|-------|-------------|
| Psychology | 12 | 56,781 | Jung, Freud, Rank |
| Mythology | 11 | 24,876 | Homer, Frazer, Bulfinch |
| Literature | 4 | 16,084 | Dostoevsky |
| **Total** | **27** | **85,157** | - |

### Graph Statistics

- 85,157 Bond nodes
- 154,393 FOLLOWS edges
- 112,137 CONTAINS edges (Book → Bond)

## Archetypes

Recognized Jungian archetypes:

| Archetype | Keywords | Meaning |
|-----------|----------|---------|
| Shadow | dark, monster, hidden, chase | Repressed self |
| Anima/Animus | woman, man, guide, mysterious | Contrasexual psyche |
| Self | center, whole, light, divine | Wholeness |
| Mother | earth, water, cave, nurturing | Maternal principle |
| Hero | journey, battle, quest, victory | Individuation |
| Death/Rebirth | dying, transform, renewal | Transformation |
| Trickster | fool, joke, chaos, boundary | Disruption |
| Wise Old Man | sage, teacher, wisdom, mountain | Inner wisdom |
