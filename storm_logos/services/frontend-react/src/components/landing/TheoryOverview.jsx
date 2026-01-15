export default function TheoryOverview() {
  return (
    <section className="landing-section prose-section">
      <div className="landing-section__content prose-content">

        <h2>The Semantic Architecture</h2>

        <p>
          When we describe the world, we combine adjectives with nouns: "fierce gods", "old house",
          "beautiful morning". These combinations — which we call <strong>bonds</strong> — are not random.
          Some nouns accept thousands of adjectives ("man" can be good, bad, old, young, tall, invisible...),
          while others accept only a handful ("tonneau" is open, folding, removable — and little else).
        </p>

        <p>
          This asymmetry suggests a hidden structure. Abstract nouns, unconstrained by physical reality,
          accept almost any modifier. Concrete nouns, bound to specific properties, resist modification.
          But is this intuition quantifiable? Does the space of adjective-noun relationships —
          <strong> Bond Space</strong> — have a precise mathematical form?
        </p>

        <p>
          We show that it does. Bond Space exhibits the same saturation dynamics as physical systems:
          it fills according to PT1 (first-order lag) kinetics, partitions into exactly five abstraction
          levels, and produces universal fractal structure. The number five is not arbitrary — it emerges
          from the mathematics of saturation itself.
        </p>

        <hr className="prose-divider" />

        <details className="prose-spoiler" open>
          <summary>The Three-Dimensional Semantic Space</summary>
          <div className="prose-spoiler__content">

            <p>
              Every word maps to three coordinates. This is not metaphor — it is measurable structure that
              emerged from processing 16,500 books and extracting millions of semantic bonds.
            </p>

            <h3>A: The Affirmation Axis</h3>
            <p>
              From −1 (negating, destructive, diminishing) to +1 (affirming, constructive, enhancing).
              "Death" has negative A. "Life" has positive A. "Create" moves toward positive A.
              "Destroy" moves toward negative A.
            </p>

            <h3>S: The Sacred Axis</h3>
            <p>
              From −1 (mundane, profane, everyday) to +1 (sacred, elevated, transcendent).
              "Chair" has low S. "God" has high S. This dimension captures the vertical axis of meaning —
              what lifts experience toward the numinous.
            </p>

            <h3>τ (Tau): The Abstraction Level</h3>
            <p>
              From 0.5 (abstract, universal, archetypal) to 4.5 (concrete, specific, particular).
              "Motion" has low τ. "Vehicle" has medium τ. "My car" has high τ.
              Dreams naturally operate at lower τ levels — more abstract, more universal, closer to
              archetypal patterns.
            </p>

            <div className="prose-formula">
              <div className="prose-formula__equation">
                Bond = (noun, adjective) → (A, S, τ)
              </div>
              <div className="prose-formula__description">
                Every bond maps to coordinates in three-dimensional semantic space
              </div>
            </div>

          </div>
        </details>

        <hr className="prose-divider" />

        <details className="prose-spoiler">
          <summary>Saturation Dynamics</summary>
          <div className="prose-spoiler__content">

            <p>
              How does Bond Space fill as we process more text? We discovered it follows the same dynamics
              as physical systems.
            </p>

            <h4>The PT1 Model</h4>

            <p>
              In PT1 (first-order lag) systems, a quantity approaches its maximum exponentially:
            </p>

            <div className="prose-formula">
              <div className="prose-formula__equation">
                y(t) = y<sub>max</sub> · (1 − e<sup>−t/τ</sup>)
              </div>
              <div className="prose-formula__description">
                First-order lag dynamics: exponential approach to asymptote
              </div>
            </div>

            {/* PT1 Saturation Curve Visualization */}
            <div className="pt1-figure">
              <div className="pt1-figure__title">Figure: PT1 Saturation Dynamics in Bond Space</div>
              <div className="pt1-figure__graph">
                <div className="pt1-figure__y-axis">
                  <span>100%</span>
                  <span>63%</span>
                  <span>0%</span>
                </div>
                <div className="pt1-figure__curve">
                  <svg viewBox="0 0 400 200" preserveAspectRatio="none">
                    {/* Grid lines */}
                    <line x1="80" y1="0" x2="80" y2="200" stroke="rgba(255,255,255,0.1)" strokeDasharray="4,4" />
                    <line x1="320" y1="0" x2="320" y2="200" stroke="rgba(255,255,255,0.1)" strokeDasharray="4,4" />
                    <line x1="0" y1="74" x2="400" y2="74" stroke="rgba(255,255,255,0.1)" strokeDasharray="4,4" />

                    {/* Asymptote line */}
                    <line x1="0" y1="10" x2="400" y2="10" stroke="rgba(99, 102, 241, 0.5)" strokeDasharray="8,4" strokeWidth="2" />

                    {/* PT1 Curve */}
                    <path
                      d="M 0 200 Q 40 100, 80 74 Q 160 30, 240 15 Q 320 8, 400 5"
                      fill="none"
                      stroke="#e94560"
                      strokeWidth="3"
                    />

                    {/* τ marker */}
                    <circle cx="80" cy="74" r="6" fill="#e94560" />
                    <text x="80" y="95" fill="var(--text-muted)" fontSize="12" textAnchor="middle">τ</text>
                    <text x="80" y="110" fill="var(--text-muted)" fontSize="10" textAnchor="middle">63%</text>

                    {/* 5τ marker */}
                    <circle cx="320" cy="12" r="6" fill="#14b8a6" />
                    <text x="320" y="35" fill="var(--text-muted)" fontSize="12" textAnchor="middle">5τ</text>
                    <text x="320" y="50" fill="var(--text-muted)" fontSize="10" textAnchor="middle">99.3%</text>
                  </svg>
                </div>
              </div>
              <div className="pt1-figure__labels">
                <span>0</span>
                <span>Nouns accumulated →</span>
                <span>∞</span>
              </div>
              <div className="pt1-figure__markers">
                <div className="pt1-figure__marker">
                  <span className="pt1-figure__marker-dot pt1-figure__marker-dot--tau"></span>
                  <span>τ = 42,921 nouns (63%)</span>
                </div>
                <div className="pt1-figure__marker">
                  <span className="pt1-figure__marker-dot pt1-figure__marker-dot--5tau"></span>
                  <span>5τ = 99.3% saturation</span>
                </div>
              </div>
            </div>

            <p>
              We propose that Bond Space follows identical dynamics, with nouns playing the role of time.
              As nouns accumulate, they fill the semantic space. Each new noun either introduces new bonds
              or activates existing ones. Early nouns — "man", "woman", "thing" — capture broad semantic
              categories. Later nouns fill increasingly specific niches.
            </p>

            <h4>Empirical Validation</h4>

            <p>
              We processed 16,500 books sequentially, tracking cumulative nouns, adjectives, and bonds.
              The result exceeded expectations. The fit achieves <strong>R² = 0.9919</strong> — near-perfect
              agreement with PT1 dynamics.
            </p>

            <table className="prose-table">
              <thead>
                <tr>
                  <th>Parameter</th>
                  <th>Value</th>
                </tr>
              </thead>
              <tbody>
                <tr>
                  <td>Asymptote (bonds/noun)</td>
                  <td>40.5</td>
                </tr>
                <tr>
                  <td>Time constant (τ)</td>
                  <td>42,921 nouns</td>
                </tr>
                <tr>
                  <td>Fit quality (R²)</td>
                  <td>0.9919</td>
                </tr>
                <tr>
                  <td>Current progress</td>
                  <td>96.2%</td>
                </tr>
              </tbody>
            </table>

            <p>
              Each noun, on average, accepts about 40 different adjectives. The space reaches 63% saturation
              after encountering 42,921 unique nouns. At 155,000 nouns, we are at 96.2% of the asymptote —
              between 3τ and 4τ in the saturation process. The semantic space is not yet fully saturated;
              we observe it as it fills.
            </p>

          </div>
        </details>

        <hr className="prose-divider" />

        <details className="prose-spoiler">
          <summary>The τ Structure: Five Levels of Abstraction</summary>
          <div className="prose-spoiler__content">

            <p>
              For each noun, we measure its <strong>variety</strong> — how many unique adjectives modify it.
              This quantity encodes semantic abstraction. When we plotted the variety distribution on log-log
              scale, we observed that order-of-magnitude divisions create meaningful semantic categories.
            </p>

            <table className="prose-table">
              <thead>
                <tr>
                  <th>Level</th>
                  <th>Variety</th>
                  <th>Count</th>
                  <th>Role</th>
                </tr>
              </thead>
              <tbody>
                <tr>
                  <td>τ₁</td>
                  <td>5000+</td>
                  <td>1</td>
                  <td>Apex ("man")</td>
                </tr>
                <tr>
                  <td>τ₂</td>
                  <td>1000-5000</td>
                  <td>297</td>
                  <td>Categories ("thing", "way", "time")</td>
                </tr>
                <tr>
                  <td>τ₃</td>
                  <td>100-1000</td>
                  <td>6,457</td>
                  <td>Concepts ("fish", "wood")</td>
                </tr>
                <tr>
                  <td>τ₄</td>
                  <td>10-100</td>
                  <td>18,684</td>
                  <td>Specifics ("battleship")</td>
                </tr>
                <tr>
                  <td>τ₅</td>
                  <td>2-10</td>
                  <td>31,656</td>
                  <td>Low variety terms</td>
                </tr>
              </tbody>
            </table>

            <p>
              At the apex sits a single noun, "man", with variety exceeding 5,000 — the most abstract entity
              in Bond Space. Below it, 297 nouns form the categorical level. The pattern continues through
              concrete concepts, specific terms, and finally low-variety nouns.
            </p>

            <h4>Why Five Levels?</h4>

            <p>
              The number five is not arbitrary. In PT1 systems, each time constant fills 63% of the remaining
              capacity. After five time constants, the system reaches 99.3% — effectively complete.
              <strong> Five abstraction levels is the natural depth of a saturating semantic space.</strong>
            </p>

          </div>
        </details>

        <hr className="prose-divider" />

        <details className="prose-spoiler">
          <summary>The Storm Algorithm</summary>
          <div className="prose-spoiler__content">

            <p>
              Navigation through semantic space uses the <strong>Storm</strong> algorithm — an explosion
              of candidate bonds from the current position, followed by dialectical filtering and
              resonance-based selection.
            </p>

            <h4>Three Sources of Candidates</h4>

            <p>
              Given current position Q in (A, S, τ) space, Storm explodes candidates from three sources:
            </p>

            <ul className="prose-list">
              <li><strong>Spatial neighbors</strong> — Bonds within radius of Q (KD-tree query)</li>
              <li><strong>Trajectory followers</strong> — Where authors went from similar positions (Neo4j edges)</li>
              <li><strong>Gravity pull</strong> — Bonds toward health (higher A, grounding τ)</li>
            </ul>

            <h4>Dialectical Filtering</h4>

            <p>
              Candidates are scored by their resonance with both thesis (current direction) and
              antithesis (opposite direction). The dialectic seeks synthesis — bonds that honor
              both poles while moving toward integration.
            </p>

            <div className="prose-formula">
              <div className="prose-formula__equation">
                score = coh<sub>thesis</sub> · (1−w) + coh<sub>antithesis</sub> · w + bonus · √(coh<sub>thesis</sub> · coh<sub>antithesis</sub>)
              </div>
              <div className="prose-formula__description">
                Dialectical scoring balances thesis, antithesis, and synthesis
              </div>
            </div>

            <h4>Chain Reaction Selection</h4>

            <p>
              Final selection uses resonance with trajectory history. Bonds that cohere with the
              conversation's semantic path receive amplification — a "lasing" effect that creates
              winner-take-all dynamics for coherent trajectories.
            </p>

          </div>
        </details>

        <hr className="prose-divider" />

        <details className="prose-spoiler">
          <summary>Archetypes as Regions</summary>
          <div className="prose-spoiler__content">

            <p>
              Jung discovered that certain images and patterns appear universally in dreams, myths, and
              religions — the Hero, the Shadow, the Anima, the Wise Old Man. These archetypes are not
              learned; they are inherited structures of the psyche.
            </p>

            <blockquote className="prose-quote">
              <p>
                "The collective unconscious contains the whole spiritual heritage of mankind's evolution,
                born anew in the brain structure of every individual."
              </p>
              <cite>— Carl Jung, The Structure of the Psyche</cite>
            </blockquote>

            <p>
              In our 3D space, archetypes manifest as <strong>regions</strong> with characteristic coordinates.
              They are not points but territories — areas where certain combinations of A, S, and τ cluster:
            </p>

            <ul className="prose-list">
              <li><strong>Hero</strong> — High A, moderate S: the path of transformation through ordeal</li>
              <li><strong>Shadow</strong> — Low A, variable S: the rejected aspects that demand integration</li>
              <li><strong>Anima/Animus</strong> — High A, high S: the inner other, gateway to wholeness</li>
              <li><strong>Self</strong> — Centered, low τ: the achieved integration of opposites</li>
              <li><strong>Wise Old Man</strong> — High S, low τ: archetypal wisdom from the depths</li>
              <li><strong>Great Mother</strong> — High A, high S: the nurturing source and devouring darkness</li>
              <li><strong>Trickster</strong> — Variable A, low S: chaos, change, creative destruction</li>
              <li><strong>Child</strong> — High A, high τ: pure potential, innocence before the fall</li>
            </ul>

            <p>
              When Storm-Logos detects archetypal presence in your dream, it shows you where you are in
              the space of meaning. The Hero's journey is not a prescription; it is a map. You choose
              your path. We help you see the territory.
            </p>

          </div>
        </details>

        <hr className="prose-divider" />

        <details className="prose-spoiler">
          <summary>Navigation, Not Prediction</summary>
          <div className="prose-spoiler__content">

            <p>
              Traditional AI asks: "What comes next?" It predicts the most probable token based on
              statistical frequency. This is prediction — following the crowd.
            </p>

            <p>
              We ask: "Where am I?" This is navigation — following a compass. The (A, S, τ) coordinates
              act as that compass, with gravity pulling toward health (higher A, grounding τ).
              Instead of predicting probable outputs, we navigate toward affirming, integrated responses.
            </p>

            <table className="prose-table">
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

            <p>
              Dream interpretation becomes navigation: understanding where you are in psychological space,
              what paths are available, and where you might want to go. The destination is not
              determined by probability but by orientation toward the good.
            </p>

          </div>
        </details>

        <details className="prose-spoiler">
          <summary>Technical Details: Validation Metrics</summary>
          <div className="prose-spoiler__content">
            <p>
              The theory has been validated through multiple independent tests:
            </p>
            <ul>
              <li><strong>PT1 Saturation</strong> — R² = 0.9919 fit to first-order lag dynamics</li>
              <li><strong>τ Correlation</strong> — r = -0.92 between τ and word frequency</li>
              <li><strong>Zipf's Law</strong> — Bond frequencies follow power-law distribution</li>
              <li><strong>Heaps' Law</strong> — Vocabulary growth follows sublinear scaling</li>
              <li><strong>Fractal Dimension</strong> — Shannon dimension D₁ {"<"} 1 across all hierarchies</li>
            </ul>
            <p>
              These are not fitted parameters but emergent properties of the semantic space.
            </p>
          </div>
        </details>

      </div>
    </section>
  )
}
