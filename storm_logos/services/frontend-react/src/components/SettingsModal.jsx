import { useState, useEffect } from 'react'
import * as api from '../api'

export default function SettingsModal({ onClose, onUserUpdate }) {
  const [user, setUser] = useState(api.getUser())
  const [displayName, setDisplayName] = useState('')
  const [avatarUrl, setAvatarUrl] = useState('')
  const [currentPassword, setCurrentPassword] = useState('')
  const [newPassword, setNewPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [profileError, setProfileError] = useState('')
  const [profileSuccess, setProfileSuccess] = useState('')
  const [passwordError, setPasswordError] = useState('')
  const [passwordSuccess, setPasswordSuccess] = useState('')

  useEffect(() => {
    loadUser()
  }, [])

  async function loadUser() {
    try {
      const data = await api.getCurrentUser()
      setUser(data)
      setDisplayName(data.display_name || '')
      setAvatarUrl(data.avatar_url || '')
    } catch (err) {
      console.error('Failed to load user:', err)
    }
  }

  async function handleProfileSubmit(e) {
    e.preventDefault()
    setProfileError('')
    setProfileSuccess('')

    try {
      await api.updateProfile(displayName || null, avatarUrl || null)
      setProfileSuccess('Profile updated successfully!')
      onUserUpdate()
    } catch (err) {
      setProfileError(err.message)
    }
  }

  async function handlePasswordSubmit(e) {
    e.preventDefault()
    setPasswordError('')
    setPasswordSuccess('')

    if (newPassword !== confirmPassword) {
      setPasswordError('New passwords do not match')
      return
    }

    try {
      await api.changePassword(currentPassword, newPassword)
      setPasswordSuccess('Password changed successfully!')
      setCurrentPassword('')
      setNewPassword('')
      setConfirmPassword('')
    } catch (err) {
      setPasswordError(err.message)
    }
  }

  async function handleResendVerification() {
    try {
      await api.resendVerification()
      alert('Verification email sent!')
    } catch (err) {
      alert(`Error: ${err.message}`)
    }
  }

  return (
    <div className="modal" onClick={(e) => e.target === e.currentTarget && onClose()}>
      <div className="modal-content large">
        <button className="close-btn" onClick={onClose}>&times;</button>
        <h2>Account Settings</h2>

        <div className="settings-section">
          <h3>Profile</h3>
          <form onSubmit={handleProfileSubmit}>
            <div className="form-group">
              <label>Display Name</label>
              <input
                type="text"
                value={displayName}
                onChange={e => setDisplayName(e.target.value)}
                placeholder="Display name"
              />
            </div>
            <div className="form-group">
              <label>Avatar URL</label>
              <input
                type="url"
                value={avatarUrl}
                onChange={e => setAvatarUrl(e.target.value)}
                placeholder="https://example.com/avatar.jpg"
              />
            </div>
            <button type="submit">Save Profile</button>
          </form>
          {profileError && <p className="error">{profileError}</p>}
          {profileSuccess && <p className="success">{profileSuccess}</p>}
        </div>

        <div className="settings-section">
          <h3>Change Password</h3>
          <form onSubmit={handlePasswordSubmit}>
            <div className="form-group">
              <label>Current Password</label>
              <input
                type="password"
                value={currentPassword}
                onChange={e => setCurrentPassword(e.target.value)}
                required
              />
            </div>
            <div className="form-group">
              <label>New Password</label>
              <input
                type="password"
                value={newPassword}
                onChange={e => setNewPassword(e.target.value)}
                required
                minLength={6}
              />
            </div>
            <div className="form-group">
              <label>Confirm New Password</label>
              <input
                type="password"
                value={confirmPassword}
                onChange={e => setConfirmPassword(e.target.value)}
                required
              />
            </div>
            <button type="submit">Change Password</button>
          </form>
          {passwordError && <p className="error">{passwordError}</p>}
          {passwordSuccess && <p className="success">{passwordSuccess}</p>}
        </div>

        <div className="settings-section">
          <h3>Account Info</h3>
          <div className="account-info">
            <p>Username: <span>{user?.username || '-'}</span></p>
            <p>Email: <span>{user?.email || 'Not set'}</span></p>
            <p>
              Email Verified: <span>{user?.email_verified ? 'Yes' : 'No'}</span>
              {user?.email && !user?.email_verified && (
                <button
                  type="button"
                  className="small"
                  onClick={handleResendVerification}
                  style={{ marginLeft: '0.5rem' }}
                >
                  Resend verification
                </button>
              )}
            </p>
            <p>Member Since: <span>{user?.created_at ? user.created_at.substring(0, 10) : '-'}</span></p>
          </div>
        </div>
      </div>
    </div>
  )
}
