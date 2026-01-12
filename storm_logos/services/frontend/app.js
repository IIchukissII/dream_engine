/**
 * Storm-Logos Frontend Application
 */

// Use direct API URL for development, /api for production (nginx proxy)
const API_BASE = window.location.port === '3000' ? 'http://localhost:8000' : '/api';

// State
let token = localStorage.getItem('token');
let user = JSON.parse(localStorage.getItem('user') || 'null');
let sessionId = null;
let isRegisterMode = false;

// DOM Elements
const authModal = document.getElementById('auth-modal');
const authForm = document.getElementById('auth-form');
const authError = document.getElementById('auth-error');
const authSuccess = document.getElementById('auth-success');
const profileModal = document.getElementById('profile-modal');
const settingsModal = document.getElementById('settings-modal');
const forgotModal = document.getElementById('forgot-modal');
const resetModal = document.getElementById('reset-modal');
const messagesContainer = document.getElementById('messages');
const messageInput = document.getElementById('message-input');
const sendBtn = document.getElementById('send-btn');
const endBtn = document.getElementById('end-btn');
const modeSelect = document.getElementById('mode-select');
const userInfo = document.getElementById('user-info');
const profileBtn = document.getElementById('profile-btn');
const settingsBtn = document.getElementById('settings-btn');
const logoutBtn = document.getElementById('logout-btn');
const emailField = document.getElementById('email');
const verifyBanner = document.getElementById('verify-banner');

// =============================================================================
// API CALLS
// =============================================================================

async function apiCall(endpoint, method = 'GET', body = null) {
    const headers = {
        'Content-Type': 'application/json',
    };
    if (token) {
        headers['Authorization'] = `Bearer ${token}`;
    }

    const options = { method, headers };
    if (body) {
        options.body = JSON.stringify(body);
    }

    const response = await fetch(`${API_BASE}${endpoint}`, options);
    const data = await response.json();

    if (!response.ok) {
        throw new Error(data.detail || 'API Error');
    }

    return data;
}

// =============================================================================
// AUTH
// =============================================================================

async function login(username, password) {
    const data = await apiCall('/auth/login', 'POST', { username, password });
    token = data.access_token;
    user = data.user;
    localStorage.setItem('token', token);
    localStorage.setItem('user', JSON.stringify(user));
    return data;
}

async function register(username, email, password) {
    const data = await apiCall('/auth/register', 'POST', { username, email, password });
    token = data.access_token;
    user = data.user;
    localStorage.setItem('token', token);
    localStorage.setItem('user', JSON.stringify(user));
    return data;
}

function logout() {
    token = null;
    user = null;
    sessionId = null;
    localStorage.removeItem('token');
    localStorage.removeItem('user');
    updateUI();
    showAuthModal();
}

async function forgotPassword(email) {
    return await apiCall('/auth/password/forgot', 'POST', { email });
}

async function resetPassword(resetToken, newPassword) {
    return await apiCall('/auth/password/reset', 'POST', { token: resetToken, new_password: newPassword });
}

async function changePassword(currentPassword, newPassword) {
    return await apiCall('/auth/password/change', 'POST', { current_password: currentPassword, new_password: newPassword });
}

async function verifyEmail(verifyToken) {
    return await apiCall('/auth/email/verify', 'POST', { token: verifyToken });
}

async function resendVerification() {
    return await apiCall('/auth/email/resend', 'POST');
}

async function updateProfile(displayName, avatarUrl) {
    const data = await apiCall('/auth/profile', 'PUT', { display_name: displayName, avatar_url: avatarUrl });
    // Update local user data
    user = { ...user, display_name: displayName, avatar_url: avatarUrl };
    localStorage.setItem('user', JSON.stringify(user));
    return data;
}

async function getCurrentUser() {
    const data = await apiCall('/auth/me', 'GET');
    user = data;
    localStorage.setItem('user', JSON.stringify(user));
    return data;
}

// =============================================================================
// SESSION
// =============================================================================

async function startSession() {
    const mode = modeSelect.value;
    const data = await apiCall('/sessions/start', 'POST', { mode: mode !== 'hybrid' ? mode : null });
    sessionId = data.session_id;
    addMessage('therapist', data.response);
    updateSessionInfo(data);
    return data;
}

async function sendMessage(message) {
    if (!sessionId) {
        await startSession();
    }

    addMessage('user', message);
    setLoading(true);

    try {
        const data = await apiCall(`/sessions/${sessionId}/message`, 'POST', { message });
        addMessage('therapist', data.response);
        updateSessionInfo(data);
        updateSidebar(data);
    } catch (error) {
        addMessage('therapist', `Error: ${error.message}`);
    } finally {
        setLoading(false);
    }
}

async function endSession() {
    if (!sessionId) return;

    setLoading(true);
    try {
        const data = await apiCall(`/sessions/${sessionId}/end`, 'POST');
        addMessage('therapist', formatEndMessage(data));
        sessionId = null;
        document.getElementById('session-mode').textContent = '-';
        document.getElementById('session-turn').textContent = '0';
    } catch (error) {
        addMessage('therapist', `Error ending session: ${error.message}`);
    } finally {
        setLoading(false);
    }
}

async function deleteSession() {
    if (!sessionId) return;

    if (!confirm('Delete this session? It will not be saved.')) return;

    setLoading(true);
    try {
        await apiCall(`/sessions/${sessionId}`, 'DELETE');
        addMessage('therapist', 'Session discarded.');
        sessionId = null;
        document.getElementById('session-mode').textContent = '-';
        document.getElementById('session-turn').textContent = '0';
        // Clear sidebar
        document.getElementById('symbols-list').innerHTML = '';
        document.getElementById('themes-list').innerHTML = '';
        document.getElementById('emotions-list').innerHTML = '';
    } catch (error) {
        addMessage('therapist', `Error deleting session: ${error.message}`);
    } finally {
        setLoading(false);
    }
}

async function pauseSession() {
    if (!sessionId) return;
    if (!token) {
        alert('Please login to pause sessions');
        return;
    }

    setLoading(true);
    try {
        const data = await apiCall(`/sessions/${sessionId}/pause`, 'POST');
        addMessage('therapist', `Session paused after ${data.turns} turns. You can resume it later from History.`);
        sessionId = null;
        document.getElementById('session-mode').textContent = '-';
        document.getElementById('session-turn').textContent = '0';
    } catch (error) {
        addMessage('therapist', `Error pausing session: ${error.message}`);
    } finally {
        setLoading(false);
    }
}

async function resumeSession(sid) {
    setLoading(true);
    try {
        const data = await apiCall(`/sessions/${sid}/resume`, 'POST');
        sessionId = data.session_id;
        addMessage('therapist', data.response);
        updateSessionInfo(data);
        updateSidebar(data);
        closeHistory();
    } catch (error) {
        addMessage('therapist', `Error resuming session: ${error.message}`);
    } finally {
        setLoading(false);
    }
}

// =============================================================================
// HISTORY
// =============================================================================

async function loadHistory() {
    if (!token) {
        alert('Please login to view session history');
        return;
    }

    try {
        const data = await apiCall('/sessions/history');
        renderHistory(data.sessions);
        document.getElementById('history-modal').classList.remove('hidden');
    } catch (error) {
        alert(`Error loading history: ${error.message}`);
    }
}

function renderHistory(sessions) {
    const list = document.getElementById('history-list');
    if (!sessions || sessions.length === 0) {
        list.innerHTML = '<p>No previous sessions found.</p>';
        return;
    }

    let html = '';
    sessions.forEach(s => {
        const date = s.timestamp ? s.timestamp.substring(0, 16).replace('T', ' ') : 'Unknown';
        const status = s.status || 'ended';
        const statusClass = status === 'paused' ? 'paused' : 'ended';
        const archetypes = (s.archetypes || []).join(', ') || 'none';

        html += `
            <div class="history-item ${statusClass}">
                <div class="history-header">
                    <span class="date">${date}</span>
                    <span class="status">${status}</span>
                </div>
                <div class="history-details">
                    <span class="mode">${s.mode}</span>
                    <span class="summary">${s.summary || ''}</span>
                </div>
                <div class="history-archetypes">Archetypes: ${archetypes}</div>
                ${status === 'paused' ? `<button onclick="resumeSession('${s.session_id}')" class="resume-btn">Resume</button>` : ''}
            </div>
        `;
    });
    list.innerHTML = html;
}

function closeHistory() {
    document.getElementById('history-modal').classList.add('hidden');
}

function formatEndMessage(data) {
    let msg = `Session complete.\n\nTurns: ${data.turns}\nSymbols: ${data.symbols.length}\n\n`;

    if (data.archetypes && data.archetypes.length > 0) {
        msg += 'Archetypes manifested:\n';
        data.archetypes.forEach(a => {
            msg += `- ${a.archetype}: ${a.symbols.join(', ')} (felt: ${a.emotions.join(', ')})\n`;
        });
    }

    msg += '\nTake care of yourself.';
    return msg;
}

// =============================================================================
// PROFILE (Archetype Profile)
// =============================================================================

async function loadProfile() {
    if (!token) {
        alert('Please login to view your profile');
        return;
    }

    try {
        const profile = await apiCall('/evolution/profile');
        renderProfile(profile);
        profileModal.classList.remove('hidden');
    } catch (error) {
        alert(`Error loading profile: ${error.message}`);
    }
}

function renderProfile(profile) {
    // Stats
    document.getElementById('profile-stats').innerHTML = `
        <div class="stat-box">
            <div class="stat-value">${profile.total_sessions}</div>
            <div class="stat-label">Sessions</div>
        </div>
        <div class="stat-box">
            <div class="stat-value">${profile.dominant_archetypes.length}</div>
            <div class="stat-label">Dominant Archetypes</div>
        </div>
    `;

    // Archetype chart
    const maxCount = Math.max(...Object.values(profile.archetypes), 1);
    let chartHtml = '';
    for (const [arch, count] of Object.entries(profile.archetypes)) {
        const pct = (count / maxCount) * 100;
        chartHtml += `
            <div class="archetype-bar">
                <span class="name">${arch}</span>
                <div class="bar">
                    <div class="fill" style="width: ${pct}%"></div>
                </div>
                <span style="margin-left: 0.5rem">${count}</span>
            </div>
        `;
    }
    document.getElementById('archetype-chart').innerHTML = chartHtml;
}

async function loadEvolution(archetype) {
    try {
        const data = await apiCall(`/evolution/archetype/${archetype}`);
        renderEvolution(data);
    } catch (error) {
        console.error('Error loading evolution:', error);
    }
}

function renderEvolution(data) {
    if (!data.length) {
        document.getElementById('evolution-list').innerHTML = '<p>No manifestations yet.</p>';
        return;
    }

    let html = '';
    data.slice(-10).forEach(item => {
        const date = item.timestamp ? item.timestamp.substring(0, 10) : 'Unknown';
        html += `
            <div class="evolution-item">
                <div class="date">${date}</div>
                <div class="symbols">Symbols: ${item.symbols.join(', ') || 'none'}</div>
                <div class="emotions">Felt: ${item.emotions.join(', ') || 'none'}</div>
            </div>
        `;
    });
    document.getElementById('evolution-list').innerHTML = html;
}

function closeProfile() {
    profileModal.classList.add('hidden');
}

// =============================================================================
// SETTINGS
// =============================================================================

async function loadSettings() {
    if (!token) {
        alert('Please login to access settings');
        return;
    }

    try {
        // Refresh user data
        await getCurrentUser();

        // Populate settings form
        document.getElementById('settings-display-name').value = user.display_name || '';
        document.getElementById('settings-avatar').value = user.avatar_url || '';

        // Account info
        document.getElementById('settings-username').textContent = user.username;
        document.getElementById('settings-email').textContent = user.email || 'Not set';
        document.getElementById('settings-verified').textContent = user.email_verified ? 'Yes' : 'No';
        document.getElementById('settings-created').textContent = user.created_at ? user.created_at.substring(0, 10) : '-';

        settingsModal.classList.remove('hidden');
    } catch (error) {
        alert(`Error loading settings: ${error.message}`);
    }
}

function closeSettings() {
    settingsModal.classList.add('hidden');
    // Clear password fields
    document.getElementById('current-password').value = '';
    document.getElementById('new-password').value = '';
    document.getElementById('confirm-password').value = '';
    // Clear messages
    hideMessage('profile-form-error');
    hideMessage('profile-form-success');
    hideMessage('password-form-error');
    hideMessage('password-form-success');
}

// =============================================================================
// FORGOT PASSWORD
// =============================================================================

function showForgotModal() {
    authModal.classList.add('hidden');
    forgotModal.classList.remove('hidden');
    hideMessage('forgot-error');
    hideMessage('forgot-success');
}

function closeForgotModal() {
    forgotModal.classList.add('hidden');
    authModal.classList.remove('hidden');
}

// =============================================================================
// PASSWORD RESET (from email link)
// =============================================================================

function showResetModal(resetToken) {
    resetModal.classList.remove('hidden');
    resetModal.dataset.token = resetToken;
    hideMessage('reset-error');
    hideMessage('reset-success');
}

function closeResetModal() {
    resetModal.classList.add('hidden');
    delete resetModal.dataset.token;
}

// =============================================================================
// EMAIL VERIFICATION
// =============================================================================

function showVerifyBanner() {
    verifyBanner.classList.remove('hidden');
}

function closeVerifyBanner() {
    verifyBanner.classList.add('hidden');
}

async function handleEmailVerification(verifyToken) {
    try {
        await verifyEmail(verifyToken);
        // Refresh user data
        await getCurrentUser();
        alert('Email verified successfully!');
        // Remove token from URL
        window.history.replaceState({}, document.title, window.location.pathname);
    } catch (error) {
        alert(`Verification failed: ${error.message}`);
    }
}

// =============================================================================
// UI UPDATES
// =============================================================================

function addMessage(type, content) {
    const div = document.createElement('div');
    div.className = `message ${type}`;
    div.innerHTML = `
        <div class="message-content">${content.replace(/\n/g, '<br>')}</div>
        <div class="message-meta">${new Date().toLocaleTimeString()}</div>
    `;
    messagesContainer.appendChild(div);
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
}

function updateSessionInfo(data) {
    document.getElementById('session-mode').textContent = data.mode || '-';
    document.getElementById('session-turn').textContent = data.turn || 0;
}

function updateSidebar(data) {
    // Symbols
    const symbolsList = document.getElementById('symbols-list');
    symbolsList.innerHTML = '';
    (data.symbols || []).forEach(s => {
        const li = document.createElement('li');
        li.innerHTML = `${s.text} ${s.archetype ? `<span class="archetype">[${s.archetype}]</span>` : ''}`;
        symbolsList.appendChild(li);
    });

    // Themes
    const themesList = document.getElementById('themes-list');
    themesList.innerHTML = '';
    (data.themes || []).forEach(t => {
        const span = document.createElement('span');
        span.className = 'tag';
        span.textContent = t;
        themesList.appendChild(span);
    });

    // Emotions
    const emotionsList = document.getElementById('emotions-list');
    emotionsList.innerHTML = '';
    (data.emotions || []).forEach(e => {
        const span = document.createElement('span');
        span.className = 'tag';
        span.textContent = e;
        emotionsList.appendChild(span);
    });
}

function updateUI() {
    if (user) {
        userInfo.textContent = user.display_name || user.username;
        profileBtn.style.display = 'block';
        settingsBtn.style.display = 'block';
        logoutBtn.style.display = 'block';
        authModal.classList.add('hidden');

        // Show verification banner if email not verified
        if (user.email && !user.email_verified) {
            showVerifyBanner();
        } else {
            closeVerifyBanner();
        }
    } else {
        userInfo.textContent = 'Guest';
        profileBtn.style.display = 'none';
        settingsBtn.style.display = 'none';
        logoutBtn.style.display = 'none';
        closeVerifyBanner();
    }
}

function showAuthModal() {
    authModal.classList.remove('hidden');
    setRegisterMode(false);
}

function setRegisterMode(isRegister) {
    isRegisterMode = isRegister;
    if (isRegister) {
        document.getElementById('auth-title').textContent = 'Create Account';
        emailField.classList.remove('hidden');
        emailField.required = true;
        document.getElementById('login-btn').textContent = 'Back to Login';
        document.getElementById('register-btn').textContent = 'Register';
    } else {
        document.getElementById('auth-title').textContent = 'Welcome';
        emailField.classList.add('hidden');
        emailField.required = false;
        document.getElementById('login-btn').textContent = 'Login';
        document.getElementById('register-btn').textContent = 'Register';
    }
}

function setLoading(isLoading) {
    if (isLoading) {
        sendBtn.disabled = true;
        sendBtn.textContent = '...';
    } else {
        sendBtn.disabled = false;
        sendBtn.textContent = 'Send';
    }
}

function showMessage(elementId, message) {
    const el = document.getElementById(elementId);
    el.textContent = message;
    el.classList.remove('hidden');
}

function hideMessage(elementId) {
    const el = document.getElementById(elementId);
    el.textContent = '';
    el.classList.add('hidden');
}

// =============================================================================
// EVENT HANDLERS
// =============================================================================

// Auth form
authForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    const username = document.getElementById('username').value;
    const password = document.getElementById('password').value;
    const email = document.getElementById('email').value;

    hideMessage('auth-error');
    hideMessage('auth-success');

    try {
        if (isRegisterMode) {
            // Switch back to login mode
            setRegisterMode(false);
        } else {
            await login(username, password);
            updateUI();
            startSession();
        }
    } catch (error) {
        showMessage('auth-error', error.message);
    }
});

document.getElementById('register-btn').addEventListener('click', async () => {
    const username = document.getElementById('username').value;
    const password = document.getElementById('password').value;
    const email = document.getElementById('email').value;

    hideMessage('auth-error');
    hideMessage('auth-success');

    if (!isRegisterMode) {
        // Switch to register mode
        setRegisterMode(true);
        return;
    }

    // Actually register
    if (!username || !password || !email) {
        showMessage('auth-error', 'Please fill in all fields');
        return;
    }

    try {
        await register(username, email, password);
        updateUI();
        startSession();
    } catch (error) {
        showMessage('auth-error', error.message);
    }
});

document.getElementById('skip-auth').addEventListener('click', () => {
    authModal.classList.add('hidden');
    startSession();
});

// Forgot password link
document.getElementById('forgot-password-link').addEventListener('click', (e) => {
    e.preventDefault();
    showForgotModal();
});

// Forgot password form
document.getElementById('forgot-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    const email = document.getElementById('forgot-email').value;

    hideMessage('forgot-error');
    hideMessage('forgot-success');

    try {
        await forgotPassword(email);
        showMessage('forgot-success', 'If that email exists, a reset link has been sent.');
    } catch (error) {
        showMessage('forgot-error', error.message);
    }
});

// Password reset form
document.getElementById('reset-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    const newPassword = document.getElementById('reset-password').value;
    const confirmPassword = document.getElementById('reset-confirm').value;
    const resetToken = resetModal.dataset.token;

    hideMessage('reset-error');
    hideMessage('reset-success');

    if (newPassword !== confirmPassword) {
        showMessage('reset-error', 'Passwords do not match');
        return;
    }

    try {
        await resetPassword(resetToken, newPassword);
        showMessage('reset-success', 'Password reset successfully! You can now login.');
        setTimeout(() => {
            closeResetModal();
            showAuthModal();
        }, 2000);
    } catch (error) {
        showMessage('reset-error', error.message);
    }
});

// Profile form (in settings)
document.getElementById('profile-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    const displayName = document.getElementById('settings-display-name').value;
    const avatarUrl = document.getElementById('settings-avatar').value;

    hideMessage('profile-form-error');
    hideMessage('profile-form-success');

    try {
        await updateProfile(displayName || null, avatarUrl || null);
        showMessage('profile-form-success', 'Profile updated successfully!');
        updateUI();
    } catch (error) {
        showMessage('profile-form-error', error.message);
    }
});

// Change password form
document.getElementById('change-password-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    const currentPassword = document.getElementById('current-password').value;
    const newPassword = document.getElementById('new-password').value;
    const confirmPassword = document.getElementById('confirm-password').value;

    hideMessage('password-form-error');
    hideMessage('password-form-success');

    if (newPassword !== confirmPassword) {
        showMessage('password-form-error', 'New passwords do not match');
        return;
    }

    try {
        await changePassword(currentPassword, newPassword);
        showMessage('password-form-success', 'Password changed successfully!');
        // Clear form
        document.getElementById('current-password').value = '';
        document.getElementById('new-password').value = '';
        document.getElementById('confirm-password').value = '';
    } catch (error) {
        showMessage('password-form-error', error.message);
    }
});

// Resend verification
document.getElementById('resend-verify-btn').addEventListener('click', async () => {
    try {
        await resendVerification();
        alert('Verification email sent!');
    } catch (error) {
        alert(`Error: ${error.message}`);
    }
});

// Send message
sendBtn.addEventListener('click', () => {
    const message = messageInput.value.trim();
    if (message) {
        sendMessage(message);
        messageInput.value = '';
    }
});

messageInput.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        sendBtn.click();
    }
});

// End session
endBtn.addEventListener('click', endSession);

// Delete session
document.getElementById('delete-btn').addEventListener('click', deleteSession);

// Pause session
document.getElementById('pause-btn').addEventListener('click', pauseSession);

// History
document.getElementById('history-btn').addEventListener('click', loadHistory);

// Profile (Archetype)
profileBtn.addEventListener('click', loadProfile);

// Settings
settingsBtn.addEventListener('click', loadSettings);

// Logout
logoutBtn.addEventListener('click', logout);

document.getElementById('archetype-select').addEventListener('change', (e) => {
    loadEvolution(e.target.value);
});

// Close modals on outside click
window.addEventListener('click', (e) => {
    if (e.target === profileModal) {
        closeProfile();
    }
    if (e.target === settingsModal) {
        closeSettings();
    }
    if (e.target === forgotModal) {
        closeForgotModal();
    }
});

// =============================================================================
// URL PARAMETER HANDLING (for email links)
// =============================================================================

function handleUrlParams() {
    const params = new URLSearchParams(window.location.search);

    // Handle email verification
    const verifyToken = params.get('verify');
    if (verifyToken) {
        handleEmailVerification(verifyToken);
    }

    // Handle password reset
    const resetToken = params.get('reset');
    if (resetToken) {
        authModal.classList.add('hidden');
        showResetModal(resetToken);
    }
}

// =============================================================================
// INIT
// =============================================================================

async function loadInfo() {
    try {
        const info = await apiCall('/info');
        document.getElementById('session-model').textContent = info.model || '-';
    } catch (error) {
        document.getElementById('session-model').textContent = 'unknown';
    }
}

// Check URL params first
handleUrlParams();

updateUI();
loadInfo();

if (!token) {
    showAuthModal();
} else {
    startSession();
}
