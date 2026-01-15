import ExpandableCard from './ExpandableCard'

export default function HowItWorks({ expandedCards, onToggle }) {
  return (
    <section className="landing-section">
      <div className="landing-section__content">
        <header className="section-header">
          <h2 className="section-header__title section-header__title--practical">
            How It Works
          </h2>
          <p className="section-header__subtitle">
            From dream to insight in five steps. Your unconscious mapped,
            your archetypes revealed, your path illuminated.
          </p>
        </header>

        {/* Steps */}
        <div className="steps-list">
          <div className="step-item">
            <div className="step-item__number">1</div>
            <div className="step-item__content">
              <h3 className="step-item__title">Share Your Dream</h3>
              <p className="step-item__description">
                Describe your dream in natural language. The more detail, the richer
                the analysis. Include symbols, emotions, actions, and settings.
              </p>
            </div>
          </div>

          <div className="step-item">
            <div className="step-item__number">2</div>
            <div className="step-item__content">
              <h3 className="step-item__title">Symbol Extraction</h3>
              <p className="step-item__description">
                Our NLP engine identifies key symbols, entities, and semantic bonds.
                Each symbol is mapped to its 16D coordinates using our trained corpus.
              </p>
            </div>
          </div>

          <div className="step-item">
            <div className="step-item__number">3</div>
            <div className="step-item__content">
              <h3 className="step-item__title">Semantic Positioning</h3>
              <p className="step-item__description">
                Your dream's overall position in j-space is computed: Affirmation (A),
                Sacredness (S), and abstraction level (&tau;). These coordinates reveal
                the dream's psychological character.
              </p>
            </div>
          </div>

          <div className="step-item">
            <div className="step-item__number">4</div>
            <div className="step-item__content">
              <h3 className="step-item__title">Archetype Detection</h3>
              <p className="step-item__description">
                We measure proximity to archetypal centroids: Shadow, Hero, Anima/Animus,
                Self, and more. The dominant archetypes indicate which psychological
                forces are active in your unconscious.
              </p>
            </div>
          </div>

          <div className="step-item">
            <div className="step-item__number">5</div>
            <div className="step-item__content">
              <h3 className="step-item__title">Guided Interpretation</h3>
              <p className="step-item__description">
                Our AI therapist, informed by your semantic coordinates and corpus
                resonances, guides you through interpretation. Drawing from Jung, Freud,
                mythology, and literature to illuminate your dream's meaning.
              </p>
            </div>
          </div>
        </div>

        {/* Validation Card */}
        <div className="card-grid card-grid--single">
          <ExpandableCard
            id="validation"
            icon="&#10003;"
            title="Scientific Validation"
            summary="The semantic space is validated against real data. &tau; correlates with word frequency at r = -0.92. Semantic clustering achieves 51% better separation than random."
            isExpanded={expandedCards['validation']}
            onToggle={onToggle}
          >
            <h4>Key Metrics</h4>
            <table className="metrics-table">
              <thead>
                <tr>
                  <th>Measure</th>
                  <th>Result</th>
                  <th>Interpretation</th>
                </tr>
              </thead>
              <tbody>
                <tr>
                  <td>&tau; vs Frequency (nouns)</td>
                  <td className="metrics-table__value">r = -0.92</td>
                  <td>Abstract words are rare, concrete common</td>
                </tr>
                <tr>
                  <td>&tau; vs Frequency (verbs)</td>
                  <td className="metrics-table__value">r = -0.95</td>
                  <td>Even stronger correlation for verbs</td>
                </tr>
                <tr>
                  <td>Semantic Clustering</td>
                  <td className="metrics-table__value">0.16 separation</td>
                  <td>51% better than random clustering</td>
                </tr>
                <tr>
                  <td>Text Quality Score</td>
                  <td className="metrics-table__value">0.292 vs 0.170</td>
                  <td>Philosophy vs random text discrimination</td>
                </tr>
              </tbody>
            </table>

            <h4>The Corpus</h4>
            <p>
              Our semantic space is derived from 27 foundational texts comprising
              85,157 semantic bonds:
            </p>
            <ul>
              <li><strong>Psychology:</strong> Jung (5 works), Freud (6 works), Otto Rank</li>
              <li><strong>Mythology:</strong> Homer, Ovid, Bulfinch, Frazer, Bible (KJV)</li>
              <li><strong>Literature:</strong> Dostoevsky (4 novels)</li>
            </ul>

            <h4>Why These Texts?</h4>
            <p>
              These works form the foundation of Western psychological and mythological
              thought. When your dream resonates with a passage from Jung or a scene from
              Homer, you're touching universal human patterns.
            </p>
          </ExpandableCard>
        </div>
      </div>
    </section>
  )
}
