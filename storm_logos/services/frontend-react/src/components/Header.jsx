export default function Header({ user, onHistory, onProfile, onSettings, onLogout, onResendVerification }) {
  return (
    <>
      {user && user.email && !user.email_verified && (
        <div className="verify-banner">
          <span>Please verify your email address.</span>
          <button className="small" onClick={onResendVerification}>
            Resend verification email
          </button>
        </div>
      )}
      <header>
        <h1>Storm-Logos</h1>
        <div className="header-right">
          <span className="user-info">{user?.display_name || user?.username || 'Guest'}</span>
          {user && (
            <div className="header-buttons">
              <button className="icon-btn" onClick={onHistory} title="History">
                📋
              </button>
              <button className="icon-btn" onClick={onSettings} title="Settings">
                ⚙️
              </button>
              <button className="icon-btn" onClick={onProfile} title="Profile">
                👤
              </button>
              <button className="icon-btn" onClick={onLogout} title="Logout">
                🚪
              </button>
            </div>
          )}
        </div>
      </header>
    </>
  )
}
