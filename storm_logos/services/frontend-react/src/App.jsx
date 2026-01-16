import { useState, useEffect } from 'react'
import * as api from './api'
import { LandingPage } from './components/landing'
import AuthModal from './components/AuthModal'
import { TermsPage, PrivacyPage } from './components/LegalPages'

const CHAT_URL = 'https://chat.dream-engine.space'

export default function App() {
  const [showAuth, setShowAuth] = useState(false)
  const [currentPage, setCurrentPage] = useState('landing')

  useEffect(() => {
    // Simple routing based on pathname
    const path = window.location.pathname
    if (path === '/terms') {
      setCurrentPage('terms')
    } else if (path === '/privacy') {
      setCurrentPage('privacy')
    } else {
      setCurrentPage('landing')
      api.trackPageView('landing')
    }
  }, [])

  // Redirect to chat app with token
  function redirectToChat(token = null) {
    const url = token ? `${CHAT_URL}?auth_token=${token}` : CHAT_URL
    window.location.href = url
  }

  // "Enter App" button handler
  function handleEnterApp() {
    const token = api.getToken()
    if (token) {
      // Already logged in, redirect with token
      redirectToChat(token)
    } else {
      // Show auth modal
      setShowAuth(true)
    }
  }

  // Login handler - redirect to chat after success
  async function handleLogin(username, password) {
    await api.login(username, password)
    redirectToChat(api.getToken())
  }

  // Register handler - redirect to chat after success
  async function handleRegister(username, email, password) {
    await api.register(username, email, password)
    redirectToChat(api.getToken())
  }

  // Skip auth - just go to chat (guest mode)
  function handleSkipAuth() {
    redirectToChat()
  }

  // Render legal pages without landing UI
  if (currentPage === 'terms') return <TermsPage />
  if (currentPage === 'privacy') return <PrivacyPage />

  return (
    <>
      {showAuth && (
        <AuthModal
          onLogin={handleLogin}
          onRegister={handleRegister}
          onSkip={handleSkipAuth}
          onClose={() => setShowAuth(false)}
        />
      )}
      <LandingPage onEnterApp={handleEnterApp} />
    </>
  )
}
