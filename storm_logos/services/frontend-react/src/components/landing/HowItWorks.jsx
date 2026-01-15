export default function HowItWorks() {
  return (
    <section className="landing-section prose-section">
      <div className="landing-section__content prose-content">

        <h2>How It Works</h2>

        <p>
          From dream to insight in five steps. Your unconscious mapped, your archetypes
          revealed, your path illuminated.
        </p>

        <hr className="prose-divider" />

        <h3>Step 1: Share Your Dream</h3>
        <p>
          Describe your dream in natural language. The more detail, the richer the analysis.
          Include symbols, emotions, actions, and settings. The unconscious speaks in images —
          capture them as vividly as you can.
        </p>

        <h3>Step 2: Symbol Extraction</h3>
        <p>
          Our NLP engine identifies key symbols, entities, and semantic bonds. Each symbol
          is mapped to its 16D coordinates using our trained corpus. "Water" is not just
          water — it has precise coordinates in j-space that connect it to emotion, the
          unconscious, transformation.
        </p>

        <h3>Step 3: Semantic Positioning</h3>
        <p>
          Your dream's overall position in j-space is computed: its Beauty, Life, Sacred,
          Good, and Love coordinates. The abstraction level (τ) reveals whether your dream
          operates at surface or archetypal depths. These coordinates reveal the dream's
          psychological character.
        </p>

        <h3>Step 4: Archetype Detection</h3>
        <p>
          We measure proximity to archetypal centroids: Shadow, Hero, Anima/Animus, Self,
          Great Mother, Wise Old Man, Trickster, Child. The dominant archetypes indicate
          which psychological forces are active in your unconscious — what patterns are
          trying to emerge into consciousness.
        </p>

        <h3>Step 5: Guided Interpretation</h3>
        <p>
          Our AI therapist, informed by your semantic coordinates and corpus resonances,
          guides you through interpretation. Drawing from Jung, Freud, mythology, and
          literature to illuminate your dream's meaning. Not prediction — navigation.
          Not diagnosis — orientation.
        </p>

        <hr className="prose-divider" />

        <h2>Scientific Validation</h2>

        <p>
          The semantic space is validated against real data. These are not fitted parameters
          but emergent properties:
        </p>

        <table className="prose-table">
          <thead>
            <tr>
              <th>Measure</th>
              <th>Result</th>
              <th>Interpretation</th>
            </tr>
          </thead>
          <tbody>
            <tr>
              <td>τ vs Frequency (nouns)</td>
              <td>r = −0.92</td>
              <td>Abstract words are rare, concrete common</td>
            </tr>
            <tr>
              <td>τ vs Frequency (verbs)</td>
              <td>r = −0.95</td>
              <td>Even stronger correlation for verbs</td>
            </tr>
            <tr>
              <td>Semantic Clustering</td>
              <td>0.16 separation</td>
              <td>51% better than random clustering</td>
            </tr>
            <tr>
              <td>PT1 Saturation Fit</td>
              <td>R² = 0.9919</td>
              <td>Near-perfect agreement with physical dynamics</td>
            </tr>
          </tbody>
        </table>

        <details className="prose-spoiler">
          <summary>The Corpus: 16,500 Books</summary>
          <div className="prose-spoiler__content">
            <p>
              Our semantic space is derived from processing 16,500 books, extracting millions
              of semantic bonds — adjective-noun pairs that reveal how language maps meaning.
            </p>
            <p>
              This massive corpus spans fiction, non-fiction, philosophy, mythology, psychology,
              and literature. The breadth ensures that Bond Space captures the full range of
              human semantic expression, from the most concrete descriptions to the most
              abstract concepts.
            </p>
            <p>
              When your dream resonates with patterns in this space, you're touching universal
              human experience — the accumulated semantic wisdom of thousands of authors
              across centuries.
            </p>
          </div>
        </details>

      </div>
    </section>
  )
}
