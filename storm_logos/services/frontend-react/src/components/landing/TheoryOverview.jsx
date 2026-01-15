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
          {/* Saturation Dynamics Card */}
          <ExpandableCard
            id="saturation"
            icon="~"
            title="Saturation Dynamics"
            summary="Bond Space fills like a physical system. PT1 dynamics govern how meaning saturates - explaining why exactly five abstraction levels exist."
            isExpanded={expandedCards['saturation']}
            onToggle={onToggle}
          >
            <h4>The Physical Analogy</h4>
            <p>
              When we combine adjectives with nouns ("fierce gods", "old house", "beautiful morning"),
              we create <em>bonds</em>. These bonds are not random. Some nouns accept thousands of
              adjectives ("man" can be good, bad, old, young, tall, invisible...), while others
              accept only a handful.
            </p>

            <h4>PT1 Dynamics: The Charging Capacitor</h4>
            <p>
              In first-order lag (PT1) systems, a quantity approaches its maximum exponentially:
            </p>
            <pre><code>{`y(t) = y_max · (1 - e^(-t/τ))

At time t = τ:   63% saturation
At time t = 5τ:  99.3% saturation`}</code></pre>

            <p>
              Bond Space follows identical dynamics. As nouns accumulate, they fill the semantic space.
              Early nouns ("man", "woman", "thing") capture broad categories. Later nouns fill
              increasingly specific niches.
            </p>

            <h4>Empirical Validation</h4>
            <table className="metrics-table">
              <thead>
                <tr>
                  <th>Parameter</th>
                  <th>Value</th>
                </tr>
              </thead>
              <tbody>
                <tr>
                  <td>Asymptote (bonds/noun)</td>
                  <td className="metrics-table__value">40.5</td>
                </tr>
                <tr>
                  <td>Time constant (&tau;)</td>
                  <td className="metrics-table__value">42,921 nouns</td>
                </tr>
                <tr>
                  <td>Fit quality (R&sup2;)</td>
                  <td className="metrics-table__value">0.9919</td>
                </tr>
                <tr>
                  <td>Current progress</td>
                  <td className="metrics-table__value">96.2%</td>
                </tr>
              </tbody>
            </table>

            <h4>Why Five Levels?</h4>
            <p>
              The number five is not arbitrary. In PT1 systems, each time constant fills 63% of
              the remaining capacity. After five time constants, the system reaches 99.3% - effectively
              complete. Five abstraction levels is the natural depth of a saturating semantic space.
            </p>
          </ExpandableCard>

          {/* The τ Structure Card */}
          <ExpandableCard
            id="tau-structure"
            icon="&#964;"
            title="The &tau; Structure"
            summary="Adjective variety partitions into discrete abstraction levels. From the apex 'man' to highly specific terms - the hierarchy of meaning."
            isExpanded={expandedCards['tau-structure']}
            onToggle={onToggle}
          >
            <h4>Measuring Abstraction</h4>
            <p>
              For each noun, we count its <em>variety</em> - how many unique adjectives modify it.
              This quantity encodes semantic abstraction. Abstract nouns like "thing" lack physical
              constraints, permitting almost any modifier. Concrete nouns like "battleship" have
              fixed properties, limiting their descriptive range.
            </p>

            <h4>The Five Levels</h4>
            <table className="metrics-table">
              <thead>
                <tr>
                  <th>Level</th>
                  <th>Variety</th>
                  <th>Role</th>
                </tr>
              </thead>
              <tbody>
                <tr>
                  <td>&tau;&#8321;</td>
                  <td className="metrics-table__value">5000+</td>
                  <td>Apex ("man")</td>
                </tr>
                <tr>
                  <td>&tau;&#8322;</td>
                  <td className="metrics-table__value">1000-5000</td>
                  <td>Categories ("thing", "way", "time")</td>
                </tr>
                <tr>
                  <td>&tau;&#8323;</td>
                  <td className="metrics-table__value">100-1000</td>
                  <td>Concepts ("fish", "wood")</td>
                </tr>
                <tr>
                  <td>&tau;&#8324;</td>
                  <td className="metrics-table__value">10-100</td>
                  <td>Specifics ("battleship")</td>
                </tr>
                <tr>
                  <td>&tau;&#8325;</td>
                  <td className="metrics-table__value">2-10</td>
                  <td>Low variety terms</td>
                </tr>
              </tbody>
            </table>

            <h4>Connection to Dreams</h4>
            <p>
              Dream symbols operate at lower &tau; levels - more abstract, more universal. When you
              dream of "falling," you're not at &tau;&#8325; (a specific fall) but at &tau;&#8322; or &tau;&#8321;
              (the archetypal Fall, the descent of consciousness). Understanding your &tau; level
              reveals the depth of meaning at play.
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
