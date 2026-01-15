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
            What is the nature of meaning itself? Before we can navigate semantic space,
            we must understand what space we are navigating - and why it exists at all.
          </p>
        </header>

        {/* Opening Quote */}
        <div style={{
          textAlign: 'center',
          margin: '2rem auto',
          maxWidth: '700px',
          padding: '2rem',
          background: 'rgba(0,0,0,0.2)',
          borderRadius: '16px'
        }}>
          <p style={{
            fontSize: '1.2rem',
            fontStyle: 'italic',
            color: 'var(--accent)',
            marginBottom: '1rem',
            letterSpacing: '0.05em'
          }}>
            "Ἐν ἀρχῇ ἦν ὁ Λόγος, καὶ ὁ Λόγος ἦν πρὸς τὸν Θεόν, καὶ Θεὸς ἦν ὁ Λόγος."
          </p>
          <p style={{ color: 'var(--text)', marginBottom: '0.5rem' }}>
            "In the beginning was the Word, and the Word was with God, and the Word was God."
          </p>
          <p style={{ fontSize: '0.9rem', color: 'var(--text-muted)' }}>
            — John 1:1
          </p>
        </div>

        <div className="card-grid">
          {/* Order, Consciousness, and the Emergence of Meaning */}
          <ExpandableCard
            id="consciousness"
            icon="&#9673;"
            title="Order, Consciousness, and Meaning"
            summary="Order does not precede consciousness as experienced order. It emerges in the act of differentiation. Chaos is reality without consciousness. Order is reality as seen by consciousness."
            isExpanded={expandedCards['consciousness']}
            onToggle={onToggle}
          >
            <p>
              Order does not precede consciousness as <em>experienced</em> order. It emerges
              in the act of differentiation.
            </p>
            <p>
              <strong>Chaos</strong> is reality without consciousness. <strong>Order</strong> is
              reality as seen by consciousness.
            </p>
            <p>
              Reality as such is not obliged to be either ordered or chaotic. These categories
              appear only where a consciousness exists that can isolate differences, hold them
              across time, and connect them into stable relationships.
            </p>
            <p>
              Without consciousness, there are processes, fluctuations, and interactions. But
              there is no form as form, no law as law, no structure as structure. Not because
              nothing exists, but because existence without meaning is not yet structure.
              This is not naive idealism, but the distinction between an ontology of processes
              and an ontology of meanings.
            </p>

            <h4>The Three Operations of Consciousness</h4>
            <p>Consciousness performs three fundamental operations:</p>
            <p>
              <strong>First, it frames:</strong> it cuts something out of continuity.
              An object is a stillness of attention.
            </p>
            <p>
              <strong>Second, it hierarchizes:</strong> it decides what is foreground and
              what is background, what is cause and what is effect, what is relevant and
              what is noise. Without this hierarchy, everything would be equivalent and
              experience would dissolve into pure entropy.
            </p>
            <p>
              <strong>Third, it connects:</strong> it transforms sequence into history,
              correlation into law, repetition into structure.
            </p>
            <p>
              In this way, order emerges not as a property of the world in itself,
              but as a stable form of meaning.
            </p>

            <h4>From Explosion Through Logos to Meaning</h4>
            <p>
              This process can be understood as a movement from <strong>Explosion</strong> through
              <strong> Logos</strong> to <strong>Meaning</strong>.
            </p>
            <p>
              The <strong>Explosion</strong> creates a field of possibilities — a storm through
              semantic space where many interpretations are excited simultaneously.
            </p>
            <p>
              <strong>Logos</strong> acts as a meaning-lens: coherence, intentionality, and
              stability select. What fits together persists; what does not is filtered out.
            </p>
            <p>
              <strong>Meaning</strong> is thereby not invented, but <em>recognized</em>.
              Understanding is not adding something new, but re-cognizing what was already
              implicitly there. In this sense, knowledge is <strong>Anamnesis</strong>:
              not learning as accumulation, but insight as remembrance.
            </p>

            <blockquote style={{
              borderLeft: '3px solid var(--accent)',
              paddingLeft: '1rem',
              margin: '1.5rem 0',
              fontStyle: 'italic',
              color: 'var(--text)'
            }}>
              Truth is the un-forgotten.
              <br /><br />
              ἀ (not) + λήθη (forgetting) = ἀλήθεια (truth)
            </blockquote>

            <h4>The Einstein-Bohr Question</h4>
            <p>
              At this point, this view touches the famous debate between Albert Einstein
              and Niels Bohr. Einstein held that reality must possess certain properties
              independent of observation. The world, he believed, is ordered even when
              no one is looking. Bohr countered that physical properties can only be
              meaningfully defined in the context of measurement and description.
              Physics does not describe reality in itself, but what appears as phenomenon
              under certain conditions.
            </p>
            <p>
              Bohr's position does not mean that consciousness creates particles. It means
              that without an act of differentiation, no determinate properties are formulable.
              Possibilities are not created from nothing, but are transformed into
              distinguishable states. In this sense, consciousness relates to reality
              similarly to observation in quantum physics: <strong>it does not create,
              but selects</strong> stable trajectories from a field of possibilities.
            </p>
            <p>
              Consciousness does not invent order — it recognizes it. Just as seeing does
              not create light but makes it visible, so consciousness does not create
              reality but makes it meaningful. If the principle of meaning ceases to be
              recognizable, reality does not "fall into chaos" — it returns to a
              pre-differentiated state in which differences have not yet been drawn,
              until a new act of differentiation arises.
            </p>
            <p>
              <strong>Reality as order is a function of consciousness.</strong> Without
              consciousness, only the potential of structures remains, but not structure as such.
            </p>
          </ExpandableCard>

          {/* The Logos and τ₀ */}
          <ExpandableCard
            id="logos"
            icon="&#937;"
            title="The Logos and τ₀"
            summary="Five centuries before John, Heraclitus spoke of a universal Logos governing all change. Our τ₀ represents this source dimension — the ground from which all meaning emanates."
            isExpanded={expandedCards['logos']}
            onToggle={onToggle}
          >
            <p>
              The Greek term <em>Logos</em> carried immense philosophical weight before
              Christianity appropriated it. For John, the Logos was not merely spoken
              language but the divine rationality that orders the cosmos — the principle
              of intelligibility itself. Everything that exists participates in Logos;
              everything that can be understood does so through Logos.
            </p>

            <blockquote style={{
              borderLeft: '3px solid var(--accent)',
              paddingLeft: '1rem',
              margin: '1.5rem 0',
              fontStyle: 'italic',
              color: 'var(--text)'
            }}>
              "This Logos holds always, but humans always prove unable to understand it,
              both before hearing it and when they have first heard it. For though all
              things come to be in accordance with this Logos, humans are like the inexperienced."
              <br /><span style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>— Heraclitus, Fragment B1</span>
            </blockquote>

            <p>
              Five centuries before John, Heraclitus spoke of a universal Logos governing
              all change and opposition. Fire transforms to water transforms to earth — yet
              the <em>measure</em> (metron) of transformation remains constant. The Logos is
              that constancy, that pattern, that rationality underlying apparent chaos.
            </p>

            <h4>τ₀: The Mathematical Logos</h4>
            <p>
              In our framework, τ₀ (tau-zero) represents the Logos computationally.
              It is the theoretical source dimension from which the entire 16-dimensional
              semantic space unfolds. The 16D space is a <em>projection</em> of τ₀ into
              manifestation. Higher τ values indicate surface meanings — further from source.
              Lower τ values approach the archetypal, the universal, the Logos itself.
              Dreams naturally operate at lower τ levels — closer to the source.
            </p>
            <p>
              We do not claim to have <em>captured</em> Logos. Rather, we have constructed
              a mathematical space in which the <em>direction toward Logos</em> can be
              meaningfully computed. The journey matters more than the destination.
            </p>

            <h4>The Thomistic Transcendentals</h4>
            <p>
              Aristotle divided being into ten categories: substance, quantity, quality,
              relation, place, time, position, state, action, passion. But what properties
              belong to <em>being as such</em>, prior to any categorical division?
            </p>
            <p>
              Medieval philosophy identified the <em>transcendentia</em> — properties
              coextensive with being itself: <strong>Unum</strong> (every being is undivided),
              <strong> Verum</strong> (every being is intelligible), <strong>Bonum</strong> (every
              being is desirable insofar as it exists), <strong>Pulchrum</strong> (every being
              pleases when perceived).
            </p>
            <p>
              When we analyzed 27 foundational texts — Homer, Dostoevsky, Jung, Freud,
              mythological corpora — and extracted principal components from 85,157
              semantic bonds, five dominant dimensions emerged that closely parallel
              the transcendentals: Beauty, Life, Sacred, Good, and Love.
            </p>
            <p>
              This convergence between medieval metaphysics and computational semantics
              suggests that the transcendentals are not arbitrary philosophical constructs
              but genuine features of the structure of meaning itself.
            </p>
          </ExpandableCard>

          {/* A Note on Faith */}
          <ExpandableCard
            id="faith"
            icon="&#10013;"
            title="A Note on Faith and Method"
            summary="This work does not claim access to absolute truth through clever argument. The key is faith — not belief without evidence, but willingness to act toward the good before proof arrives."
            isExpanded={expandedCards['faith']}
            onToggle={onToggle}
          >
            <p>
              I understand that this perspective will meet resistance. In our era of
              constructivism and postmodernism, it has become difficult to speak of
              reality at all — everything dissolves into interpretation, perspective,
              power relations. The very concept of truth seems naive or dangerous.
            </p>
            <p>
              But this work does not claim access to absolute truth through clever argument.
              The key to this work is <strong>faith</strong>. Not faith as belief without
              evidence, but faith as the willingness to act toward the good before proof arrives.
            </p>

            <blockquote style={{
              borderLeft: '3px solid var(--accent)',
              paddingLeft: '1rem',
              margin: '1.5rem 0',
              fontStyle: 'italic',
              color: 'var(--text)'
            }}>
              Only lived faith becomes knowledge.
              <br /><br />
              Experience is the path of faith. Faith is the fruit of experience.
              The circle closes — but only for those who walk it.
            </blockquote>

            <h4>What We Are Building</h4>
            <p>
              This is not a claim to have discovered profound truth. It is a <em>path</em> —
              an attempt to build tools that help consciousness perform its differentiation
              work more clearly:
            </p>
            <ul>
              <li>A semantic space where words have <em>positions</em>, not just associations</li>
              <li>A physics of meaning where concepts have gravity, temperature, coherence</li>
              <li>Navigation algorithms that move toward <em>good</em>, not just toward probable</li>
              <li>Intent-driven collapse where verbs act as operators that focus exploration</li>
            </ul>
            <p>
              The question is not whether this is "true" in some absolute sense. The question
              is whether these tools help us <strong>see more clearly</strong>, <strong>navigate
              more wisely</strong>, and <strong>understand more deeply</strong>.
            </p>
          </ExpandableCard>
        </div>
      </div>
    </section>
  )
}
