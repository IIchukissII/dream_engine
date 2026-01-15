import { useState, useEffect, useRef } from 'react'
import HeroSection from './HeroSection'
import TheoryOverview from './TheoryOverview'
import OntologicalFoundation from './OntologicalFoundation'
import HowItWorks from './HowItWorks'
import InteractiveDemo from './InteractiveDemo'
import SectionNav from './SectionNav'
import './landing.css'

const SECTION_NAMES = [
  'Welcome',
  'Theory',
  'Philosophy',
  'How It Works',
  'Get Started'
]

export default function LandingPage({ onEnterApp }) {
  const [activeSection, setActiveSection] = useState(0)
  const [expandedCards, setExpandedCards] = useState({})
  const containerRef = useRef(null)
  const sectionsRef = useRef([])

  // Toggle expandable card
  const toggleCard = (cardId) => {
    setExpandedCards(prev => ({
      ...prev,
      [cardId]: !prev[cardId]
    }))
  }

  // Scroll to specific section
  const scrollToSection = (index) => {
    sectionsRef.current[index]?.scrollIntoView({ behavior: 'smooth' })
  }

  // Scroll to theory section
  const scrollToTheory = () => {
    scrollToSection(1)
  }

  // Intersection Observer for active section tracking
  useEffect(() => {
    const options = {
      root: containerRef.current,
      threshold: 0.5
    }

    const observer = new IntersectionObserver((entries) => {
      entries.forEach(entry => {
        if (entry.isIntersecting) {
          const index = sectionsRef.current.indexOf(entry.target)
          if (index !== -1) {
            setActiveSection(index)
          }
        }
      })
    }, options)

    sectionsRef.current.forEach(section => {
      if (section) observer.observe(section)
    })

    return () => observer.disconnect()
  }, [])

  // Keyboard navigation
  useEffect(() => {
    const handleKeyDown = (e) => {
      if (e.key === 'ArrowDown' || e.key === 'PageDown') {
        e.preventDefault()
        const nextSection = Math.min(activeSection + 1, SECTION_NAMES.length - 1)
        scrollToSection(nextSection)
      } else if (e.key === 'ArrowUp' || e.key === 'PageUp') {
        e.preventDefault()
        const prevSection = Math.max(activeSection - 1, 0)
        scrollToSection(prevSection)
      } else if (e.key === 'Home') {
        e.preventDefault()
        scrollToSection(0)
      } else if (e.key === 'End') {
        e.preventDefault()
        scrollToSection(SECTION_NAMES.length - 1)
      }
    }

    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [activeSection])

  return (
    <div className="landing-page" ref={containerRef}>
      <SectionNav
        activeSection={activeSection}
        sectionNames={SECTION_NAMES}
        onNavigate={scrollToSection}
      />

      <div ref={el => sectionsRef.current[0] = el}>
        <HeroSection
          onScrollToTheory={scrollToTheory}
          onEnterApp={onEnterApp}
        />
      </div>

      <div ref={el => sectionsRef.current[1] = el}>
        <TheoryOverview
          expandedCards={expandedCards}
          onToggle={toggleCard}
        />
      </div>

      <div ref={el => sectionsRef.current[2] = el}>
        <OntologicalFoundation
          expandedCards={expandedCards}
          onToggle={toggleCard}
        />
      </div>

      <div ref={el => sectionsRef.current[3] = el}>
        <HowItWorks
          expandedCards={expandedCards}
          onToggle={toggleCard}
        />
      </div>

      <div ref={el => sectionsRef.current[4] = el}>
        <InteractiveDemo onEnterApp={onEnterApp} />
      </div>
    </div>
  )
}
