export default function SectionNav({ activeSection, sectionNames, onNavigate }) {
  return (
    <nav className="section-nav">
      {sectionNames.map((name, index) => (
        <div
          key={index}
          className={`section-nav__dot ${activeSection === index ? 'section-nav__dot--active' : ''}`}
          onClick={() => onNavigate(index)}
        >
          <span className="section-nav__tooltip">{name}</span>
        </div>
      ))}
    </nav>
  )
}
