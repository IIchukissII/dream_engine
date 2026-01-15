export default function HeroSection({ onScrollToTheory, onEnterApp }) {
  return (
    <section className="landing-section hero-section">
      <div className="hero-particles" />

      <img
        src="/logo.svg"
        alt="Storm-Logos"
        className="hero-logo"
        onError={(e) => { e.target.style.display = 'none' }}
      />

      <h1 className="hero-title">Storm-Logos</h1>

      <p className="hero-subtitle">Navigate Your Psyche Through Dreams</p>

      <p className="hero-vision">
        A 16-dimensional semantic space where ancient wisdom meets modern AI.
        Not prediction, but navigation. Not statistics, but meaning.
        Map the landscape of your unconscious mind.
      </p>

      <div className="hero-cta-group">
        <button className="hero-cta hero-cta--primary" onClick={onScrollToTheory}>
          Explore the Theory
        </button>
        <button className="hero-cta hero-cta--secondary" onClick={onEnterApp}>
          Enter the Engine
        </button>
      </div>

      <div className="scroll-indicator" onClick={onScrollToTheory}>
        <span>Discover More</span>
        <span className="scroll-indicator__arrow">&#8595;</span>
      </div>
    </section>
  )
}
