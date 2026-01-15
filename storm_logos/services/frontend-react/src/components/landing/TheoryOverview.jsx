import ExpandableCard from './ExpandableCard'

export default function TheoryOverview({ expandedCards, onToggle }) {
  return (
    <section className="landing-section">
      <div className="landing-section__content">
        <header className="section-header">
          <h2 className="section-header__title section-header__title--theory">
            The Semantic Architecture
          </h2>
          <p className="section-header__subtitle">
            Understanding meaning through geometry. Your psyche exists in a rich
            16-dimensional space where every thought has coordinates.
          </p>
        </header>

        {/* Dimension Visualizer */}
        <div className="dimension-viz">
          <div className="dimension-viz__item">
            <div className="dimension-viz__value dimension-viz__value--j">5</div>
            <div className="dimension-viz__label">Dimensions</div>
            <div className="dimension-viz__name">j-space</div>
          </div>
          <div className="dimension-viz__item">
            <div className="dimension-viz__value dimension-viz__value--i">11</div>
            <div className="dimension-viz__label">Dimensions</div>
            <div className="dimension-viz__name">i-space</div>
          </div>
          <div className="dimension-viz__item">
            <div className="dimension-viz__value dimension-viz__value--tau">1</div>
            <div className="dimension-viz__label">Dimension</div>
            <div className="dimension-viz__name">&tau; (tau)</div>
          </div>
        </div>

        <div className="card-grid">
          {/* Saturation Mechanics Card */}
          <ExpandableCard
            id="saturation"
            icon="~"
            title="Saturation Mechanics"
            summary="Every word carries a semantic charge that saturates meaning. Like a capacitor charging, concepts accumulate semantic energy until they reach equilibrium."
            isExpanded={expandedCards['saturation']}
            onToggle={onToggle}
          >
            <h4>The RC-Model of Meaning</h4>
            <p>
              Semantic saturation follows an RC-circuit model: each word acts as a capacitor
              that charges with meaning from context. The saturation level determines how
              strongly a concept influences its neighbors.
            </p>

            <h4>Key Principles</h4>
            <ul>
              <li><strong>Charge:</strong> Words accumulate semantic weight from surrounding context</li>
              <li><strong>Discharge:</strong> Meaning dissipates over textual distance</li>
              <li><strong>Equilibrium:</strong> The system finds balance at characteristic time constants</li>
              <li><strong>Resonance:</strong> Similar concepts amplify each other's charge</li>
            </ul>

            <h4>Mathematical Formulation</h4>
            <pre><code>{`dS/dt = -S/RC + Input(t)

Where:
  S = Semantic saturation level
  RC = Characteristic time constant
  Input(t) = Contextual semantic input`}</code></pre>

            <p>
              This explains why repeated themes in dreams intensify their meaning,
              and why distant symbols can still resonate through semantic fields.
            </p>
          </ExpandableCard>

          {/* The 16D Space Card */}
          <ExpandableCard
            id="16d-space"
            icon="&#8734;"
            title="The 16-Dimensional Space"
            summary="Your psyche maps to 16 dimensions: 5 transcendental (j-space), 11 contextual (i-space), plus abstraction level (&tau;)."
            isExpanded={expandedCards['16d-space']}
            onToggle={onToggle}
          >
            <h4>j-space: The Transcendentals (5D)</h4>
            <p>
              The core of meaning - five fundamental qualities that exist independently
              of context. These are the invariant dimensions:
            </p>
            <div className="transcendentals-list">
              <div className="transcendental-item">
                <div className="transcendental-item__name">Beauty</div>
                <div className="transcendental-item__latin">Pulchrum</div>
              </div>
              <div className="transcendental-item">
                <div className="transcendental-item__name">Life</div>
                <div className="transcendental-item__latin">Esse</div>
              </div>
              <div className="transcendental-item">
                <div className="transcendental-item__name">Sacred</div>
                <div className="transcendental-item__latin">Unum</div>
              </div>
              <div className="transcendental-item">
                <div className="transcendental-item__name">Good</div>
                <div className="transcendental-item__latin">Bonum</div>
              </div>
              <div className="transcendental-item">
                <div className="transcendental-item__name">Love</div>
                <div className="transcendental-item__latin">Amor</div>
              </div>
            </div>

            <h4>i-space: Surface Dimensions (11D)</h4>
            <p>
              The contextual layer - dimensions that vary with situation: Truth, Freedom,
              Meaning, Order, Peace, Power, Nature, Time, Knowledge, Self, Society.
            </p>

            <h4>&tau; (Tau): Abstraction Level</h4>
            <p>
              From concrete (&tau;=6: "my car") to archetypal (&tau;=1: "The Vehicle of the Soul").
              Dreams often operate at lower &tau; levels - more abstract, more universal.
            </p>
          </ExpandableCard>

          {/* Navigation vs Prediction Card */}
          <ExpandableCard
            id="navigation"
            icon="&#8594;"
            title="Navigation, Not Prediction"
            summary="Traditional AI predicts the next token by statistics. We navigate through semantic space toward meaning itself."
            isExpanded={expandedCards['navigation']}
            onToggle={onToggle}
          >
            <h4>The Paradigm Shift</h4>
            <table className="metrics-table">
              <thead>
                <tr>
                  <th>Traditional AI</th>
                  <th>Semantic Navigation</th>
                </tr>
              </thead>
              <tbody>
                <tr>
                  <td>"What comes next?"</td>
                  <td>"Where am I?"</td>
                </tr>
                <tr>
                  <td>Statistical frequency</td>
                  <td>Geometric position</td>
                </tr>
                <tr>
                  <td>Follow the crowd</td>
                  <td>Follow the compass</td>
                </tr>
                <tr>
                  <td>Determinism</td>
                  <td>Freedom</td>
                </tr>
              </tbody>
            </table>

            <h4>The Compass</h4>
            <p>
              j-space acts as a compass - pointing toward transcendent meaning.
              Instead of predicting probable outputs, we navigate toward good,
              beautiful, alive, sacred, loving responses.
            </p>

            <h4>Implications for Dreams</h4>
            <p>
              Dream interpretation becomes navigation: understanding where you are
              in psychological space, what paths (verbs) are available, and where
              you might want to go.
            </p>
          </ExpandableCard>
        </div>
      </div>
    </section>
  )
}
