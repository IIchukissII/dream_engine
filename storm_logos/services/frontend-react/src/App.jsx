import { useState, useEffect } from 'react'
import * as api from './api'
import { LandingPage } from './components/landing'
import AuthModal from './components/AuthModal'
import Header from './components/Header'
import Sidebar from './components/Sidebar'
import Chat from './components/Chat'
import HistoryModal from './components/HistoryModal'
import ProfileModal from './components/ProfileModal'
import SettingsModal from './components/SettingsModal'
import BooksTab from './components/BooksTab'
import DreamTab from './components/DreamTab'
import AdminDashboard from './components/AdminDashboard'

export default function App() {
  // Landing page state - always show on initial visit
  const [showLanding, setShowLanding] = useState(true)

  const [activeTab, setActiveTab] = useState('chat')
  const [user, setUser] = useState(api.getUser())
  const [sessionId, setSessionId] = useState(null)
  const [sessionInfo, setSessionInfo] = useState({ mode: '-', turn: 0, model: '-' })
  const [messages, setMessages] = useState([])
  const [symbols, setSymbols] = useState([])
  const [themes, setThemes] = useState([])
  const [emotions, setEmotions] = useState([])
  const [loading, setLoading] = useState(false)
  const [showAuth, setShowAuth] = useState(!api.getToken())
  const [showHistory, setShowHistory] = useState(false)
  const [showProfile, setShowProfile] = useState(false)
  const [showSettings, setShowSettings] = useState(false)
  const [verificationSuccess, setVerificationSuccess] = useState(false)
  const [verificationError, setVerificationError] = useState(null)

  // Handler to exit landing page and enter the app
  function handleEnterApp() {
    setShowLanding(false)
    api.trackPageView('app')
  }

  // Handler to show landing page again (for Theory link)
  function handleShowTheory() {
    setShowLanding(true)
  }

  useEffect(() => {
    loadInfo()
    handleEmailVerification()
    if (api.getToken()) {
      handleStartSession()
    }
  }, [])

  async function handleEmailVerification() {
    const params = new URLSearchParams(window.location.search)
    const path = window.location.pathname

    // Handle email verification - supports both /auth/verify-email?token= and ?verify=
    const verifyToken = params.get('token') && path.includes('verify-email')
      ? params.get('token')
      : params.get('verify')

    if (verifyToken) {
      // Always exit landing page when processing verification
      setShowLanding(false)

      try {
        await api.verifyEmail(verifyToken)
        // Refresh user data to get updated email_verified status
        if (api.getToken()) {
          const updatedUser = await api.getCurrentUser()
          setUser(updatedUser)
        }
        setVerificationSuccess(true)
      } catch (err) {
        setVerificationError(err.message)
      }
      // Clean up URL after processing
      window.history.replaceState({}, document.title, '/')
    }
  }

  async function loadInfo() {
    try {
      const info = await api.getInfo()
      setSessionInfo(prev => ({ ...prev, model: info.model }))
    } catch (e) {
      console.error('Failed to load info:', e)
    }
  }

  async function handleLogin(username, password) {
    await api.login(username, password)
    setUser(api.getUser())
    setShowAuth(false)
    handleStartSession()
  }

  async function handleRegister(username, email, password) {
    await api.register(username, email, password)
    setUser(api.getUser())
    setShowAuth(false)
    handleStartSession()
  }

  function handleLogout() {
    api.logout()
    setUser(null)
    setSessionId(null)
    setMessages([])
    setShowAuth(true)
  }

  function handleSkipAuth() {
    setShowAuth(false)
    handleStartSession()
  }

  function handleUserUpdate() {
    setUser(api.getUser())
  }

  async function handleResendVerification() {
    try {
      await api.resendVerification()
      alert('Verification email sent!')
    } catch (err) {
      alert(`Error: ${err.message}`)
    }
  }

  async function handleStartSession(mode = null) {
    setLoading(true)
    try {
      const data = await api.startSession(mode)
      setSessionId(data.session_id)
      setSessionInfo(prev => ({ ...prev, mode: data.mode, turn: data.turn }))
      addMessage('therapist', data.response)
    } catch (e) {
      addMessage('therapist', `Error: ${e.message}`)
    } finally {
      setLoading(false)
    }
  }

  function addMessage(type, content) {
    setMessages(prev => [...prev, { type, content, time: new Date().toLocaleTimeString() }])
  }

  async function handleSendMessage(message, mode = null) {
    if (!sessionId) {
      await handleStartSession()
    }
    addMessage('user', message)
    setLoading(true)
    try {
      // Pass mode to API - enables full theory-based response generation
      const data = await api.sendMessage(sessionId, message, mode)
      addMessage('therapist', data.response)
      setSessionInfo(prev => ({ ...prev, mode: data.mode, turn: data.turn }))
      setSymbols(data.symbols || [])
      setThemes(data.themes || [])
      setEmotions(data.emotions || [])
    } catch (e) {
      addMessage('therapist', `Error: ${e.message}`)
    } finally {
      setLoading(false)
    }
  }

  async function handleEndSession() {
    if (!sessionId) return
    setLoading(true)
    try {
      const data = await api.endSession(sessionId)
      let msg = `Session complete.\n\nTurns: ${data.turns}\nSymbols: ${data.symbols.length}\n\n`
      if (data.archetypes?.length > 0) {
        msg += 'Archetypes manifested:\n'
        data.archetypes.forEach(a => {
          msg += `- ${a.archetype}: ${a.symbols.join(', ')} (felt: ${a.emotions.join(', ')})\n`
        })
      }
      addMessage('therapist', msg)
      setSessionId(null)
      setSessionInfo(prev => ({ ...prev, mode: '-', turn: 0 }))
      setSymbols([])
      setThemes([])
      setEmotions([])
    } catch (e) {
      addMessage('therapist', `Error: ${e.message}`)
    } finally {
      setLoading(false)
    }
  }

  async function handlePauseSession() {
    if (!sessionId || !api.getToken()) return
    setLoading(true)
    try {
      const data = await api.pauseSession(sessionId)
      addMessage('therapist', `Session paused after ${data.turns} turns. Resume from History.`)
      setSessionId(null)
      setSessionInfo(prev => ({ ...prev, mode: '-', turn: 0 }))
    } catch (e) {
      addMessage('therapist', `Error: ${e.message}`)
    } finally {
      setLoading(false)
    }
  }

  async function handleDeleteSession() {
    if (!sessionId) return
    if (!confirm('Delete this session?')) return
    setLoading(true)
    try {
      await api.deleteSession(sessionId)
      addMessage('therapist', 'Session discarded.')
      setSessionId(null)
      setSessionInfo(prev => ({ ...prev, mode: '-', turn: 0 }))
      setSymbols([])
      setThemes([])
      setEmotions([])
    } catch (e) {
      addMessage('therapist', `Error: ${e.message}`)
    } finally {
      setLoading(false)
    }
  }

  async function handleResumeSession(sid) {
    setLoading(true)
    try {
      const data = await api.resumeSession(sid)
      setSessionId(data.session_id)
      addMessage('therapist', data.response)
      setSessionInfo(prev => ({ ...prev, mode: data.mode, turn: data.turn }))
      setSymbols(data.symbols || [])
      setThemes(data.themes || [])
      setEmotions(data.emotions || [])
      setShowHistory(false)
    } catch (e) {
      addMessage('therapist', `Error: ${e.message}`)
    } finally {
      setLoading(false)
    }
  }

  // Show landing page for first-time visitors
  if (showLanding) {
    return <LandingPage onEnterApp={handleEnterApp} />
  }

  return (
    <div id="app">
      {showAuth && (
        <AuthModal
          onLogin={handleLogin}
          onRegister={handleRegister}
          onSkip={handleSkipAuth}
        />
      )}

      {showHistory && (
        <HistoryModal
          onClose={() => setShowHistory(false)}
          onResume={handleResumeSession}
        />
      )}

      {showProfile && (
        <ProfileModal onClose={() => setShowProfile(false)} />
      )}

      {showSettings && (
        <SettingsModal
          onClose={() => setShowSettings(false)}
          onUserUpdate={handleUserUpdate}
        />
      )}

      {(verificationSuccess || verificationError) && (
        <div className="modal" onClick={() => {
          setVerificationSuccess(false)
          setVerificationError(null)
        }}>
          <div className="modal-content verification-modal" onClick={e => e.stopPropagation()}>
            {verificationSuccess ? (
              <>
                <div className="verification-icon success">&#10003;</div>
                <h2>Email Verified!</h2>
                <p>Your account has been successfully activated.</p>
                <p>You now have full access to all features.</p>
                <button onClick={() => setVerificationSuccess(false)}>
                  Continue to App
                </button>
              </>
            ) : (
              <>
                <div className="verification-icon error">&#10007;</div>
                <h2>Verification Failed</h2>
                <p>{verificationError}</p>
                <p>The link may have expired or already been used.</p>
                <button onClick={() => setVerificationError(null)}>
                  Close
                </button>
              </>
            )}
          </div>
        </div>
      )}

      <Header
        user={user}
        onHistory={() => setShowHistory(true)}
        onProfile={() => setShowProfile(true)}
        onSettings={() => setShowSettings(true)}
        onLogout={handleLogout}
        onResendVerification={handleResendVerification}
        onShowTheory={handleShowTheory}
      />

      <div className="tabs">
        <button
          className={`tab ${activeTab === 'chat' ? 'active' : ''}`}
          onClick={() => setActiveTab('chat')}
        >
          Session
        </button>
        <button
          className={`tab ${activeTab === 'dream' ? 'active' : ''}`}
          onClick={() => setActiveTab('dream')}
        >
          Dream
        </button>
        <button
          className={`tab ${activeTab === 'books' ? 'active' : ''}`}
          onClick={() => setActiveTab('books')}
        >
          Library
        </button>
        {user?.is_superuser && (
          <button
            className={`tab ${activeTab === 'admin' ? 'active' : ''}`}
            onClick={() => setActiveTab('admin')}
          >
            Admin
          </button>
        )}
      </div>

      <main>
        {activeTab === 'chat' && (
          <>
            <Sidebar
              sessionInfo={sessionInfo}
              symbols={symbols}
              themes={themes}
              emotions={emotions}
            />
            <Chat
              messages={messages}
              loading={loading}
              onSend={handleSendMessage}
              onEnd={handleEndSession}
              onPause={handlePauseSession}
              onDelete={handleDeleteSession}
            />
          </>
        )}
        {activeTab === 'dream' && <DreamTab />}
        {activeTab === 'books' && <BooksTab user={user} />}
        {activeTab === 'admin' && <AdminDashboard user={user} />}
      </main>
    </div>
  )
}
