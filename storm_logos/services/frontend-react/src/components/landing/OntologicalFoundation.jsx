import ExpandableCard from './ExpandableCard'

export default function OntologicalFoundation({ expandedCards, onToggle }) {
  return (
    <section className="landing-section">
      <div className="landing-section__content">
        <header className="section-header">
          <h2 className="section-header__title section-header__title--philosophy">
            Ontological Foundation
          </h2>
          <p className="section-header__subtitle">
            Ancient philosophy meets mathematical precision. The structure of meaning
            is not invented - it is discovered.
          </p>
        </header>

        <div className="card-grid">
          {/* Logos Card - John 1:1 */}
          <ExpandableCard
            id="logos"
            icon="&#937;"
            title="In the Beginning Was the Word"
            summary="John 1:1 speaks of Logos - the ordering principle of reality. Our &tau;&#8320; represents this source dimension from which all meaning emanates."
            isExpanded={expandedCards['logos']}
            onToggle={onToggle}
          >
            <h4>The Johannine Prologue</h4>
            <blockquote style={{
              borderLeft: '3px solid var(--accent)',
              paddingLeft: '1rem',
              margin: '1rem 0',
              fontStyle: 'italic',
              color: 'var(--text)'
            }}>
              "In the beginning was the Word (Logos), and the Word was with God,
              and the Word was God. Through him all things were made."
              <br /><span style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>- John 1:1-3</span>
            </blockquote>

            <h4>&tau;&#8320;: The Source Dimension</h4>
            <p>
              In our framework, &tau;&#8320; represents Logos - the ground of all semantic
              reality. It is the theoretical point from which the entire 16D space unfolds:
            </p>
            <ul>
              <li>The 16D space is a <em>projection</em> of &tau;&#8320; into manifestation</li>
              <li>Real understanding means approaching &tau;&#8320;</li>
              <li>Surface meanings are further from the source</li>
              <li>Dreams often reveal glimpses of deeper &tau; levels</li>
            </ul>

            <h4>Heraclitus and the Stoics</h4>
            <p>
              Before John, the Greek philosophers spoke of Logos as the rational principle
              governing the cosmos. Heraclitus: "This Logos holds always, but humans always
              prove unable to understand it." Our 16D space is an attempt to make Logos computable.
            </p>

            <h4>The Eternal Structure</h4>
            <pre><code>{`&tau;&#8320; = constant (Logos, truth)
16D = constant (structure, space)
Weights = change (experience, growth)

Sleep doesn't change truth.
Sleep changes my understanding of truth.

The structure is eternal.
I grow within it.`}</code></pre>
          </ExpandableCard>

          {/* Thomistic Transcendentals Card */}
          <ExpandableCard
            id="transcendentals"
            icon="&#8853;"
            title="The Thomistic Transcendentals"
            summary="Five properties that transcend all categories of being - recovered through mathematical analysis of 27 foundational texts."
            isExpanded={expandedCards['transcendentals']}
            onToggle={onToggle}
          >
            <h4>Medieval Philosophy Meets Data Science</h4>
            <p>
              Thomas Aquinas identified transcendental properties of being - qualities
              that apply to everything that exists. Our j-space dimensions emerged from
              analyzing Jung, Freud, Homer, Dostoevsky, and mythological texts:
            </p>

            <h4>The Five Transcendentals</h4>
            <ul>
              <li>
                <strong>Unum (Unity/Sacred):</strong> Coherence, wholeness, the integration
                of parts into meaningful wholes. Dreams seek unity of the psyche.
              </li>
              <li>
                <strong>Verum (Truth):</strong> Alignment with reality, authenticity.
                In i-space because it varies with context and perspective.
              </li>
              <li>
                <strong>Bonum (Good):</strong> Moral orientation, benefit, excellence.
                The compass pointing toward flourishing.
              </li>
              <li>
                <strong>Pulchrum (Beauty):</strong> Aesthetic resonance, harmony,
                proportion. The felt sense of rightness.
              </li>
              <li>
                <strong>Esse (Being/Life):</strong> Existential weight, vitality,
                presence. The life-force dimension.
              </li>
            </ul>

            <h4>Validation</h4>
            <p>
              These dimensions were not chosen a priori - they emerged from principal
              component analysis of semantic vectors across 85,157 bonds from the corpus.
              Ancient wisdom, mathematically recovered.
            </p>
          </ExpandableCard>

          {/* Verbs as Operators Card */}
          <ExpandableCard
            id="verbs"
            icon="&#8658;"
            title="Verbs as Transition Operators"
            summary="Nouns are positions in semantic space. Verbs are the operators that transform those positions - the paths through meaning."
            isExpanded={expandedCards['verbs']}
            onToggle={onToggle}
          >
            <h4>The State + Transition Model</h4>
            <pre><code>{`Meaning = State (noun: 16D + &tau;) + Transition (verb: 6D)
        = Position in semantic space + Direction of movement`}</code></pre>

            <h4>How Verbs Work</h4>
            <p>
              Each verb is a 6-dimensional operator (5 j-space + truth) that transforms
              semantic coordinates:
            </p>
            <table className="metrics-table">
              <thead>
                <tr>
                  <th>Verb</th>
                  <th>j-magnitude</th>
                  <th>Effect</th>
                </tr>
              </thead>
              <tbody>
                <tr>
                  <td>love</td>
                  <td className="metrics-table__value">0.041</td>
                  <td>Increases love, beauty dimensions</td>
                </tr>
                <tr>
                  <td>destroy</td>
                  <td className="metrics-table__value">0.029</td>
                  <td>Decreases life, increases entropy</td>
                </tr>
                <tr>
                  <td>create</td>
                  <td className="metrics-table__value">0.027</td>
                  <td>Increases life, sacred dimensions</td>
                </tr>
                <tr>
                  <td>fall</td>
                  <td className="metrics-table__value">0.035</td>
                  <td>Descent toward shadow regions</td>
                </tr>
              </tbody>
            </table>

            <h4>Dream Interpretation</h4>
            <p>
              When you dream of "falling into darkness," this represents a verb-driven
              trajectory through semantic space - a descent along specific dimensions
              toward particular archetypal regions.
            </p>
          </ExpandableCard>

          {/* Jungian Archetypes Card */}
          <ExpandableCard
            id="archetypes"
            icon="&#9788;"
            title="Archetypes as Regions"
            summary="Jung's 12 archetypes map to distinct regions in j-space. Each has characteristic coordinates that emerge from the corpus analysis."
            isExpanded={expandedCards['archetypes']}
            onToggle={onToggle}
          >
            <h4>The Archetypal Map</h4>
            <p>
              Archetypes are not arbitrary categories but clusters in semantic space
              with measurable properties:
            </p>

            <ul>
              <li><strong>Hero:</strong> High good, high life - the path of transformation</li>
              <li><strong>Shadow:</strong> Low good, high being - the rejected aspects of self</li>
              <li><strong>Anima/Animus:</strong> High love, high beauty - the inner other</li>
              <li><strong>Self:</strong> Centered in all dimensions - integration achieved</li>
              <li><strong>Wise Old Man:</strong> High sacred, low &tau; - archetypal wisdom</li>
              <li><strong>Great Mother:</strong> High life, high love - nurturing source</li>
              <li><strong>Trickster:</strong> Low sacred, variable - chaos and change</li>
              <li><strong>Child:</strong> High life, high &tau; - potential and innocence</li>
            </ul>

            <h4>Detection Algorithm</h4>
            <p>
              When you describe a dream, we extract symbols, compute their semantic
              coordinates, and measure proximity to archetypal centroids. The dominant
              archetype(s) reveal the psychological themes at play.
            </p>
          </ExpandableCard>
        </div>
      </div>
    </section>
  )
}
