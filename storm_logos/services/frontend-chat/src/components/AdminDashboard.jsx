import { useState, useEffect } from 'react'
import * as api from '../api'

export default function AdminDashboard({ user }) {
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [sortBy, setSortBy] = useState('created_at')
  const [sortOrder, setSortOrder] = useState('desc')
  const [search, setSearch] = useState('')

  useEffect(() => {
    loadUsers()
  }, [])

  async function loadUsers() {
    try {
      const result = await api.getAdminUsers()
      if (result.error) {
        setError(result.error)
      } else {
        setData(result)
      }
    } catch (e) {
      setError(e.message)
    } finally {
      setLoading(false)
    }
  }

  if (!user?.is_superuser) {
    return (
      <div className="admin-dashboard">
        <div className="admin-error">Access denied. Superuser privileges required.</div>
      </div>
    )
  }

  if (loading) {
    return <div className="admin-dashboard"><p className="loading-text">Loading user data...</p></div>
  }

  if (error) {
    return <div className="admin-dashboard"><p className="error-text">{error}</p></div>
  }

  const summary = data?.summary || {}
  const users = data?.users || []

  // Filter and sort users
  const filteredUsers = users
    .filter(u => {
      if (!search) return true
      const q = search.toLowerCase()
      return (u.username || '').toLowerCase().includes(q) ||
             (u.email || '').toLowerCase().includes(q) ||
             (u.display_name || '').toLowerCase().includes(q)
    })
    .sort((a, b) => {
      let aVal, bVal
      switch (sortBy) {
        case 'username':
          aVal = (a.username || '').toLowerCase()
          bVal = (b.username || '').toLowerCase()
          return sortOrder === 'asc' ? aVal.localeCompare(bVal) : bVal.localeCompare(aVal)
        case 'email':
          aVal = (a.email || '').toLowerCase()
          bVal = (b.email || '').toLowerCase()
          return sortOrder === 'asc' ? aVal.localeCompare(bVal) : bVal.localeCompare(aVal)
        case 'verified':
          aVal = a.email_verified ? 1 : 0
          bVal = b.email_verified ? 1 : 0
          return sortOrder === 'asc' ? aVal - bVal : bVal - aVal
        case 'activity':
          aVal = a.total_activity || 0
          bVal = b.total_activity || 0
          return sortOrder === 'asc' ? aVal - bVal : bVal - aVal
        case 'sessions':
          aVal = a.session_count || 0
          bVal = b.session_count || 0
          return sortOrder === 'asc' ? aVal - bVal : bVal - aVal
        case 'dreams':
          aVal = a.dream_count || 0
          bVal = b.dream_count || 0
          return sortOrder === 'asc' ? aVal - bVal : bVal - aVal
        case 'created_at':
        default:
          aVal = a.created_at || ''
          bVal = b.created_at || ''
          return sortOrder === 'asc' ? aVal.localeCompare(bVal) : bVal.localeCompare(aVal)
      }
    })

  function toggleSort(field) {
    if (sortBy === field) {
      setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc')
    } else {
      setSortBy(field)
      setSortOrder('desc')
    }
  }

  function formatDate(isoString) {
    if (!isoString) return '-'
    try {
      return new Date(isoString).toLocaleDateString()
    } catch {
      return isoString.split('T')[0]
    }
  }

  return (
    <div className="admin-dashboard">
      <div className="admin-header">
        <h2>Admin Dashboard</h2>
        <button onClick={loadUsers} className="refresh-btn">Refresh</button>
      </div>

      <div className="admin-summary">
        <div className="summary-card">
          <div className="summary-value">{summary.total_users || 0}</div>
          <div className="summary-label">Total Users</div>
        </div>
        <div className="summary-card">
          <div className="summary-value">{summary.verified_users || 0}</div>
          <div className="summary-label">Verified</div>
        </div>
        <div className="summary-card">
          <div className="summary-value">{summary.unverified_users || 0}</div>
          <div className="summary-label">Unverified</div>
        </div>
        <div className="summary-card">
          <div className="summary-value">{summary.total_sessions || 0}</div>
          <div className="summary-label">Sessions</div>
        </div>
        <div className="summary-card">
          <div className="summary-value">{summary.total_dreams || 0}</div>
          <div className="summary-label">Dreams</div>
        </div>
      </div>

      <div className="admin-controls">
        <input
          type="text"
          placeholder="Search users..."
          value={search}
          onChange={e => setSearch(e.target.value)}
          className="search-input"
        />
        <span className="user-count">{filteredUsers.length} users</span>
      </div>

      <div className="admin-table-container">
        <table className="admin-table">
          <thead>
            <tr>
              <th onClick={() => toggleSort('username')} className="sortable">
                Username {sortBy === 'username' && (sortOrder === 'asc' ? '↑' : '↓')}
              </th>
              <th onClick={() => toggleSort('email')} className="sortable">
                Email {sortBy === 'email' && (sortOrder === 'asc' ? '↑' : '↓')}
              </th>
              <th onClick={() => toggleSort('verified')} className="sortable">
                Verified {sortBy === 'verified' && (sortOrder === 'asc' ? '↑' : '↓')}
              </th>
              <th onClick={() => toggleSort('sessions')} className="sortable">
                Sessions {sortBy === 'sessions' && (sortOrder === 'asc' ? '↑' : '↓')}
              </th>
              <th onClick={() => toggleSort('dreams')} className="sortable">
                Dreams {sortBy === 'dreams' && (sortOrder === 'asc' ? '↑' : '↓')}
              </th>
              <th onClick={() => toggleSort('activity')} className="sortable">
                Activity {sortBy === 'activity' && (sortOrder === 'asc' ? '↑' : '↓')}
              </th>
              <th onClick={() => toggleSort('created_at')} className="sortable">
                Joined {sortBy === 'created_at' && (sortOrder === 'asc' ? '↑' : '↓')}
              </th>
            </tr>
          </thead>
          <tbody>
            {filteredUsers.map(u => (
              <tr key={u.user_id}>
                <td className="username-cell">
                  {u.display_name || u.username}
                  {u.display_name && <span className="username-sub">@{u.username}</span>}
                </td>
                <td className="email-cell">{u.email || '-'}</td>
                <td className="verified-cell">
                  <span className={`status-badge ${u.email_verified ? 'verified' : 'unverified'}`}>
                    {u.email_verified ? 'Yes' : 'No'}
                  </span>
                </td>
                <td className="number-cell">{u.session_count || 0}</td>
                <td className="number-cell">{u.dream_count || 0}</td>
                <td className="number-cell activity-cell">{u.total_activity || 0}</td>
                <td className="date-cell">{formatDate(u.created_at)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {filteredUsers.length === 0 && (
        <div className="empty-state-box">
          <p>No users found</p>
        </div>
      )}
    </div>
  )
}
