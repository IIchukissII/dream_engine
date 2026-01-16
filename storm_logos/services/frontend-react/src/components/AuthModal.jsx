import { useState, useEffect } from 'react'
import * as api from '../api'

export default function AuthModal({ onLogin, onRegister, onSkip, onClose }) {
  const [mode, setMode] = useState('login') // 'login', 'register', 'forgot', 'reset'
  const [username, setUsername] = useState('')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')
  const [resetToken, setResetToken] = useState('')
  const [agreedToTerms, setAgreedToTerms] = useState(false)

  // Check URL for reset token on mount
  useEffect(() => {
    const params = new URLSearchParams(window.location.search)
    const token = params.get('reset')
    if (token) {
      setResetToken(token)
      setMode('reset')
    }
    // Note: email verification is now handled in App.jsx to work for logged-in users too
  }, [])

  async function handleVerifyEmail(token) {
    try {
      await api.verifyEmail(token)
      setSuccess('Email verified successfully!')
      window.history.replaceState({}, document.title, window.location.pathname)
    } catch (err) {
      setError(`Verification failed: ${err.message}`)
    }
  }

  async function handleSubmit(e) {
    e.preventDefault()
    setError('')
    setSuccess('')

    if (mode === 'login') {
      try {
        await onLogin(username, password)
      } catch (err) {
        setError(err.message)
      }
    } else if (mode === 'register') {
      if (!username || !email || !password) {
        setError('Please fill in all fields')
        return
      }
      if (!agreedToTerms) {
        setError('Please agree to the Terms of Service and Privacy Policy')
        return
      }
      try {
        await onRegister(username, email, password)
      } catch (err) {
        setError(err.message)
      }
    } else if (mode === 'forgot') {
      if (!email) {
        setError('Please enter your email')
        return
      }
      try {
        await api.forgotPassword(email)
        setSuccess('If that email exists, a reset link has been sent.')
      } catch (err) {
        setError(err.message)
      }
    } else if (mode === 'reset') {
      if (password !== confirmPassword) {
        setError('Passwords do not match')
        return
      }
      try {
        await api.resetPassword(resetToken, password)
        setSuccess('Password reset successfully! You can now login.')
        setTimeout(() => {
          setMode('login')
          setSuccess('')
          window.history.replaceState({}, document.title, window.location.pathname)
        }, 2000)
      } catch (err) {
        setError(err.message)
      }
    }
  }

  function switchMode(newMode) {
    setMode(newMode)
    setError('')
    setSuccess('')
    setAgreedToTerms(false)
  }

  return (
    <div className="modal" onClick={onClose}>
      <div className="modal-content" onClick={e => e.stopPropagation()}>
        {onClose && (
          <button className="modal-close" onClick={onClose} type="button">&times;</button>
        )}
        <h2>
          {mode === 'login' && 'Welcome'}
          {mode === 'register' && 'Create Account'}
          {mode === 'forgot' && 'Reset Password'}
          {mode === 'reset' && 'Set New Password'}
        </h2>

        {mode === 'forgot' && (
          <p className="modal-subtitle">Enter your email to receive a password reset link.</p>
        )}

        <form onSubmit={handleSubmit}>
          {(mode === 'login' || mode === 'register') && (
            <input
              type="text"
              placeholder="Username"
              value={username}
              onChange={e => setUsername(e.target.value)}
              required
            />
          )}

          {(mode === 'register' || mode === 'forgot') && (
            <input
              type="email"
              placeholder="Email"
              value={email}
              onChange={e => setEmail(e.target.value)}
              required
            />
          )}

          {mode !== 'forgot' && (
            <input
              type="password"
              placeholder={mode === 'reset' ? 'New password' : 'Password'}
              value={password}
              onChange={e => setPassword(e.target.value)}
              required
              minLength={6}
            />
          )}

          {mode === 'reset' && (
            <input
              type="password"
              placeholder="Confirm password"
              value={confirmPassword}
              onChange={e => setConfirmPassword(e.target.value)}
              required
            />
          )}

          {mode === 'login' && (
            <>
              <div className="auth-buttons">
                <button type="submit">Login</button>
                <button type="button" onClick={() => switchMode('register')}>Register</button>
              </div>
              <div className="auth-links">
                <a href="#" onClick={(e) => { e.preventDefault(); switchMode('forgot'); }}>
                  Forgot password?
                </a>
              </div>
              <button type="button" className="secondary" onClick={onSkip}>
                Continue as Guest
              </button>
            </>
          )}

          {mode === 'register' && (
            <>
              <label className="checkbox-label">
                <input
                  type="checkbox"
                  checked={agreedToTerms}
                  onChange={e => setAgreedToTerms(e.target.checked)}
                />
                <span>
                  I agree to the{' '}
                  <a href="/terms" target="_blank" rel="noopener noreferrer">Terms of Service</a>
                  {' '}and{' '}
                  <a href="/privacy" target="_blank" rel="noopener noreferrer">Privacy Policy</a>
                </span>
              </label>
              <div className="auth-buttons">
                <button type="button" onClick={() => switchMode('login')}>Back to Login</button>
                <button type="submit">Register</button>
              </div>
              <button type="button" className="secondary" onClick={onSkip}>
                Continue as Guest
              </button>
            </>
          )}

          {mode === 'forgot' && (
            <>
              <button type="submit">Send Reset Link</button>
              <button type="button" className="secondary" onClick={() => switchMode('login')}>
                Back to Login
              </button>
            </>
          )}

          {mode === 'reset' && (
            <button type="submit">Reset Password</button>
          )}
        </form>

        {error && <p className="error">{error}</p>}
        {success && <p className="success">{success}</p>}
      </div>
    </div>
  )
}
