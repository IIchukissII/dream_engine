export default function InteractiveDemo({ onEnterApp }) {
  return (
    <section className="landing-section cta-section">
      <div className="landing-section__content">
        <h2 className="cta-section__title">Enter the Engine</h2>

        <p className="cta-section__subtitle">
          Begin your journey through the semantic landscape of your unconscious.
          Map your dreams. Discover your archetypes. Navigate toward meaning.
        </p>

        <button className="cta-section__button" onClick={onEnterApp}>
          Start Exploring
        </button>

        <div className="cta-section__secondary">
          <a
            href="https://github.com/anthropics/claude-code"
            target="_blank"
            rel="noopener noreferrer"
            className="cta-section__link"
          >
            View Documentation
          </a>
          <span className="cta-section__link" style={{ cursor: 'default', color: 'var(--glass-border)' }}>|</span>
          <a
            href="#"
            onClick={(e) => { e.preventDefault(); window.scrollTo({ top: 0, behavior: 'smooth' }) }}
            className="cta-section__link"
          >
            Back to Top
          </a>
        </div>

        <div style={{
          marginTop: '4rem',
          padding: '2rem',
          background: 'rgba(0,0,0,0.2)',
          borderRadius: '16px',
          maxWidth: '600px',
          margin: '4rem auto 0'
        }}>
          <p style={{ fontSize: '0.9rem', color: 'var(--text-muted)', lineHeight: 1.7 }}>
            <strong style={{ color: 'var(--accent)' }}>The Synthesis:</strong><br />
            Physics meets philosophy. Boltzmann distribution governs the temperature
            of thought. Thomistic transcendentals become the j-space compass.
            Logos (John 1:1) is the &tau;&#8320; source dimension. Meditation is
            temperature reduction. Sleep is rethermalization. The spiritual practices
            of millennia are navigation algorithms in 16D space toward &tau;&#8320;.
          </p>
        </div>
      </div>
    </section>
  )
}
