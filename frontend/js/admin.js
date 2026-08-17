document.addEventListener('DOMContentLoaded', () => {
  const loginForm = document.getElementById('admin-login-form');
  const passwordInput = document.getElementById('admin-password');
  const backendUrlInput = document.getElementById('admin-backend-url');
  const errorMsg = document.getElementById('login-error');
  
  const screenLogin = document.getElementById('screen-admin-login');
  const screenDashboard = document.getElementById('screen-admin-dashboard');
  const currentBackendDisplay = document.getElementById('current-backend-display');

  const btnPlayGame = document.getElementById('btn-play-game');
  const btnLogout = document.getElementById('btn-logout');
  const btnRefresh = document.getElementById('btn-refresh');
  const btnExport = document.getElementById('btn-export');
  const btnReset = document.getElementById('btn-reset');

  // Live Control Elements
  const statusBadge = document.getElementById('admin-game-status-badge');
  const connectedCountEl = document.getElementById('admin-connected-count');
  const roundTimerRow = document.getElementById('round-timer-row');
  const roundElapsedEl = document.getElementById('admin-round-elapsed');

  const btnAdminStart = document.getElementById('btn-admin-start-game');
  const btnAdminStartR1 = document.getElementById('btn-admin-start-r1');
  const btnAdminStartR2 = document.getElementById('btn-admin-start-r2');
  const btnAdminStartR3 = document.getElementById('btn-admin-start-r3');
  const btnAdminStop = document.getElementById('btn-admin-stop-game');
  const btnAdminResetLobby = document.getElementById('btn-admin-reset-lobby');
  
  let pollingInterval;
  let roundTimerInterval;
  let currentGameState = { status: 'waiting', roundNumber: 0, startTime: null };

  const getBaseUrl = () => {
    const stored = sessionStorage.getItem('GAME_API_URL') || localStorage.getItem('GAME_API_URL');
    if (stored) return stored.replace(/\/+$/, '');
    if (typeof GameConfig !== 'undefined' && GameConfig.api && GameConfig.api.baseUrl) {
      return GameConfig.api.baseUrl.replace(/\/+$/, '');
    }
    return window.location.origin || 'http://localhost:3000';
  };

  // Prefill backend URL input if available
  if (backendUrlInput) {
    backendUrlInput.value = sessionStorage.getItem('GAME_API_URL') || localStorage.getItem('GAME_API_URL') || '';
  }

  // Initialize Socket.io
  let socket = null;
  function initSocket() {
    const baseUrl = getBaseUrl();
    if (typeof io !== 'undefined') {
      try {
        socket = baseUrl.startsWith('http') ? io(baseUrl) : io();
        socket.on('connected_clients', (data) => {
          if (connectedCountEl && data) {
            connectedCountEl.textContent = data.count || 0;
          }
        });

        socket.on('game_state', (state) => {
          handleGameStateUpdate(state);
        });

        socket.on('game_started', (state) => {
          handleGameStateUpdate(state);
        });

        socket.on('game_ended', (state) => {
          handleGameStateUpdate(state);
        });

        socket.on('leaderboard_update', () => {
          if (sessionStorage.getItem('adminToken')) {
            loadDashboardData();
          }
        });
      } catch (err) {
        console.warn('[Socket Init Warning]:', err);
      }
    }
  }

  initSocket();

  // Check if already logged in via sessionStorage
  const token = sessionStorage.getItem('adminToken');
  if (token) {
    showDashboard();
    loadDashboardData();
  }

  loginForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    const password = passwordInput.value.trim();
    const customBackend = backendUrlInput ? backendUrlInput.value.trim() : '';

    if (customBackend) {
      const cleanUrl = customBackend.replace(/\/+$/, '');
      sessionStorage.setItem('GAME_API_URL', cleanUrl);
      localStorage.setItem('GAME_API_URL', cleanUrl);
      if (typeof GameConfig !== 'undefined' && GameConfig.api) {
        GameConfig.api.baseUrl = cleanUrl;
      }
      initSocket();
    }

    const apiUrl = getBaseUrl();
    errorMsg.classList.add('hidden');
    
    try {
      const res = await fetch(`${apiUrl}/api/admin/login`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ password })
      });
      
      const contentType = res.headers.get('content-type') || '';
      if (!contentType.includes('application/json')) {
        throw new Error(`Server at ${apiUrl} did not return JSON. Is your Game Server running at this URL?`);
      }

      const data = await res.json();
      if (res.ok && (data.success || data.gameState)) {
        sessionStorage.setItem('adminToken', password);
        errorMsg.classList.add('hidden');
        showDashboard();
        if (data.gameState) {
          handleGameStateUpdate(data.gameState);
        }
        loadDashboardData();
      } else {
        errorMsg.textContent = data.detail || data.error || data.message || 'Invalid password';
        errorMsg.classList.remove('hidden');
      }
    } catch (err) {
      errorMsg.textContent = err.message || 'Network error connecting to Backend. Please verify Backend API URL.';
      errorMsg.classList.remove('hidden');
    }
  });

  btnLogout.addEventListener('click', () => {
    sessionStorage.removeItem('adminToken');
    clearInterval(pollingInterval);
    clearInterval(roundTimerInterval);
    screenDashboard.classList.remove('screen-active');
    screenDashboard.classList.add('screen-hidden');
    screenLogin.classList.remove('screen-hidden');
    screenLogin.classList.add('screen-active');
    passwordInput.value = '';
  });

  btnPlayGame.addEventListener('click', () => {
    window.open('/flipcard', '_blank');
  });

  btnRefresh.addEventListener('click', loadDashboardData);

  // ------------------------------------------------------------------------
  // Live Event Game Controls
  // ------------------------------------------------------------------------
  async function startBroadcastRound(roundNum) {
    const token = sessionStorage.getItem('adminToken');
    if (!token) return;

    if (btnAdminStart) btnAdminStart.disabled = true;
    if (btnAdminStartR1) btnAdminStartR1.disabled = true;
    if (btnAdminStartR2) btnAdminStartR2.disabled = true;
    if (btnAdminStartR3) btnAdminStartR3.disabled = true;

    try {
      const res = await fetch(`${getBaseUrl()}/api/admin/game/start`, {
        method: 'POST',
        headers: { 
          'Content-Type': 'application/json',
          'x-admin-password': token 
        },
        body: JSON.stringify(roundNum ? { roundNumber: Number(roundNum), round_number: Number(roundNum) } : {})
      });
      const data = await res.json();
      const state = data.gameState || data.state || data;
      if (res.ok && state) {
        handleGameStateUpdate(state);
      } else {
        alert(data.detail || data.error || 'Failed to start game round');
      }
    } catch (e) {
      alert('Network error starting round');
    }
  }

  btnAdminStart?.addEventListener('click', () => startBroadcastRound(null));
  btnAdminStartR1?.addEventListener('click', () => startBroadcastRound(1));
  btnAdminStartR2?.addEventListener('click', () => startBroadcastRound(2));
  btnAdminStartR3?.addEventListener('click', () => startBroadcastRound(3));

  btnAdminStop?.addEventListener('click', async () => {
    const token = sessionStorage.getItem('adminToken');
    if (!token) return;

    if (!confirm('🛑 End the current game round now? Students will not be able to submit further ranked scores.')) {
      return;
    }

    if (btnAdminStop) btnAdminStop.disabled = true;
    try {
      const res = await fetch(`${getBaseUrl()}/api/admin/game/stop`, {
        method: 'POST',
        headers: { 'x-admin-password': token }
      });
      const data = await res.json();
      const state = data.gameState || data.state || data;
      if (res.ok && state) {
        handleGameStateUpdate(state);
      } else {
        alert(data.detail || data.error || 'Failed to stop game round');
      }
    } catch (e) {
      alert('Network error stopping round');
    }
  });

  btnAdminResetLobby?.addEventListener('click', async () => {
    const token = sessionStorage.getItem('adminToken');
    if (!token) return;

    try {
      const res = await fetch(`${getBaseUrl()}/api/admin/game/reset-lobby`, {
        method: 'POST',
        headers: { 'x-admin-password': token }
      });
      const data = await res.json();
      const state = data.gameState || data.state || data;
      if (res.ok && state) {
        handleGameStateUpdate(state);
      }
    } catch (e) {
      alert('Network error resetting lobby');
    }
  });

  function handleGameStateUpdate(state) {
    if (!state) return;
    currentGameState = state;

    if (connectedCountEl && state.connectedClients !== undefined) {
      connectedCountEl.textContent = state.connectedClients;
    }

    // Update Status Badge & Buttons
    statusBadge.className = 'admin-badge';
    clearInterval(roundTimerInterval);

    const isPlay = state.status === 'playing';
    if (btnAdminStart) btnAdminStart.disabled = isPlay;
    if (btnAdminStartR1) btnAdminStartR1.disabled = isPlay;
    if (btnAdminStartR2) btnAdminStartR2.disabled = isPlay;
    if (btnAdminStartR3) btnAdminStartR3.disabled = isPlay;
    if (btnAdminStop) btnAdminStop.disabled = !isPlay;

    if (state.status === 'waiting') {
      statusBadge.classList.add('badge-waiting');
      statusBadge.innerHTML = '🟡 LOBBY OPEN (WAITING)';
      roundTimerRow.classList.add('hidden');
    } else if (state.status === 'playing') {
      statusBadge.classList.add('badge-playing');
      const roundN = state.roundNumber || 1;
      const stageN = roundN === 1 ? 'CARDS' : (roundN === 2 ? 'JIGSAW' : 'SLIDER');
      statusBadge.innerHTML = `🟢 STAGE ${roundN} (${stageN}) LIVE`;
      roundTimerRow.classList.remove('hidden');

      // Start elapsed timer
      startElapsedTimer(state.startTime);
    } else if (state.status === 'ended') {
      statusBadge.classList.add('badge-ended');
      statusBadge.innerHTML = `🔴 ROUND #${state.roundNumber || 1} ENDED`;
      roundTimerRow.classList.add('hidden');
    }
  }

  function startElapsedTimer(startTime) {
    if (!startTime) return;
    const update = () => {
      const elapsedSec = Math.floor((Date.now() - startTime) / 1000);
      const mm = String(Math.floor(elapsedSec / 60)).padStart(2, '0');
      const ss = String(elapsedSec % 60).padStart(2, '0');
      roundElapsedEl.textContent = `${mm}:${ss}`;
    };
    update();
    roundTimerInterval = setInterval(update, 1000);
  }

  btnExport.addEventListener('click', async () => {
    const token = sessionStorage.getItem('adminToken');
    if (!token) return;
    
    try {
      const res = await fetch(`${getBaseUrl()}/api/admin/export-csv`, {
        headers: {
          'x-admin-password': token
        }
      });
      if (res.ok) {
        const blob = await res.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = 'event_leaderboard_export.csv';
        document.body.appendChild(a);
        a.click();
        a.remove();
        window.URL.revokeObjectURL(url);
      } else {
        alert('Failed to export CSV. Unauthorized?');
      }
    } catch (e) {
      alert('Network error while exporting.');
    }
  });

  btnReset.addEventListener('click', async () => {
    const token = sessionStorage.getItem('adminToken');
    if (!token) return;

    if (!confirm('⚠️ Are you sure you want to clear all player scores from the database?')) {
      return;
    }

    try {
      const res = await fetch(`${getBaseUrl()}/api/admin/reset`, {
        method: 'POST',
        headers: {
          'x-admin-password': token
        }
      });
      const data = await res.json();
      if (res.ok && data.success) {
        alert('Leaderboard reset successfully!');
        loadDashboardData();
      } else {
        alert(data.error || 'Failed to reset leaderboard.');
      }
    } catch (e) {
      alert('Network error while resetting.');
    }
  });

  function showDashboard() {
    screenLogin.classList.remove('screen-active');
    screenLogin.classList.add('screen-hidden');
    screenDashboard.classList.remove('screen-hidden');
    screenDashboard.classList.add('screen-active');
    
    if (currentBackendDisplay) {
      currentBackendDisplay.textContent = getBaseUrl();
    }

    clearInterval(pollingInterval);
    pollingInterval = setInterval(loadDashboardData, 10000);
  }

  async function loadDashboardData() {
    const token = sessionStorage.getItem('adminToken');
    if (!token) {
      btnLogout.click();
      return;
    }

    try {
      const res = await fetch(`${getBaseUrl()}/api/admin/scores`, {
        headers: {
          'x-admin-password': token
        }
      });
      
      if (res.status === 401) {
        btnLogout.click();
        return;
      }
      
      const data = await res.json();
      if (data) {
        if (data.gameState) {
          handleGameStateUpdate(data.gameState);
        }
        
        const stats = data.stats || {};
        const players = data.players || (Array.isArray(data.entries) ? data.entries.map((e, idx) => ({
          rank: idx + 1,
          playerName: e.player_name,
          score: e.score,
          durationMs: e.duration_ms,
          matches: e.matches,
          mismatches: e.mismatches,
          createdAt: e.created_at
        })) : []);

        updateStats({
          totalPlayers: stats.totalPlayers ?? stats.total_players ?? players.length,
          highestScore: stats.highestScore ?? stats.top_score ?? 0,
          avgDurationSec: stats.avgDurationSec ?? (stats.average_duration_ms ? Math.round(stats.average_duration_ms / 1000) : 0)
        });
        renderTable(players);
      }
    } catch (e) {
      console.error('Failed to load admin data:', e);
    }
  }

  function updateStats(stats) {
    document.getElementById('stat-total-players').textContent = stats.totalPlayers || 0;
    document.getElementById('stat-highest-score').textContent = stats.highestScore || 0;
    document.getElementById('stat-avg-time').textContent = (stats.avgDurationSec || 0) + 's';
  }

  function renderTable(players) {
    const tbody = document.getElementById('admin-leaderboard-body');
    
    if (players.length === 0) {
      tbody.innerHTML = `
        <tr>
          <td colspan="7" class="loading-cell">No player submissions found yet.</td>
        </tr>
      `;
      return;
    }

    tbody.innerHTML = players.map(p => {
      const durationSec = Math.round((p.durationMs || 0) / 1000);
      const timeStr = new Date(p.createdAt).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });
      let medal = p.rank;
      if (p.rank === 1) medal = '🥇 #1';
      else if (p.rank === 2) medal = '🥈 #2';
      else if (p.rank === 3) medal = '🥉 #3';
      else medal = `#${p.rank}`;

      return `
        <tr>
          <td style="font-family: var(--font-heading); font-weight: 800;">${medal}</td>
          <td style="font-weight: 800;">${p.playerName}</td>
          <td style="font-family: var(--font-heading); font-weight: 900; color: var(--bg-primary); font-size: 1.05rem;">${p.score}</td>
          <td>${durationSec}s</td>
          <td style="color: #16a34a;">${p.matches || 9}</td>
          <td style="color: #dc2626;">${p.mismatches || 0}</td>
          <td style="color: var(--text-muted); font-size: 0.82rem;">${timeStr}</td>
        </tr>
      `;
    }).join('');
  }
});
