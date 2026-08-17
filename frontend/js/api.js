/**
 * API Client Module
 * Resilient REST communication with built-in timeouts and network error isolation.
 */
class ApiClient {
  constructor(config) {
    this.config = config || (typeof GameConfig !== 'undefined' ? GameConfig : {});
  }

  get baseUrl() {
    return (this.config.api && this.config.api.baseUrl) ? this.config.api.baseUrl : '';
  }

  get timeoutMs() {
    return (this.config.api && this.config.api.timeoutMs) ? this.config.api.timeoutMs : 8000;
  }

  async request(endpoint, options = {}) {
    const url = `${this.baseUrl}${endpoint}`;
    const controller = new AbortController();
    const timer = setTimeout(() => controller.abort(), this.timeoutMs);

    const defaultHeaders = {
      'Content-Type': 'application/json',
      'Accept': 'application/json'
    };

    try {
      const response = await fetch(url, {
        ...options,
        signal: controller.signal,
        headers: {
          ...defaultHeaders,
          ...(options.headers || {})
        }
      });

      clearTimeout(timer);

      const data = await response.json().catch(() => ({}));
      if (!response.ok) {
        const error = new Error(data.detail || data.error || data.message || `HTTP ${response.status}`);
        error.status = response.status;
        error.data = data;
        throw error;
      }

      return data;
    } catch (err) {
      clearTimeout(timer);
      const isTimeout = err.name === 'AbortError';
      const isNetwork = !window.navigator.onLine || err.message === 'Failed to fetch' || isTimeout;

      const customError = new Error(
        isTimeout ? 'Request timed out' : (isNetwork ? 'Network unavailable' : err.message)
      );
      customError.isTimeout = isTimeout;
      customError.isNetwork = isNetwork;
      customError.originalError = err;
      throw customError;
    }
  }

  // Start game session
  async startGame(playerName) {
    return this.request('/api/game/start', {
      method: 'POST',
      body: JSON.stringify({
        playerName,
        player_name: playerName
      })
    });
  }

  // Submit final score
  async submitScore({ sessionId, playerName, actions }) {
    const act = actions || {};
    return this.request('/api/game/score', {
      method: 'POST',
      body: JSON.stringify({
        sessionId,
        session_id: sessionId,
        playerName,
        player_name: playerName,
        matches: act.matches || 0,
        mismatches: act.mismatches || 0,
        roundsCompleted: act.roundsCompleted || 3,
        rounds_completed: act.roundsCompleted || 3,
        durationMs: act.durationMs || 0,
        duration_ms: act.durationMs || 0,
        actions: act
      })
    });
  }

  // Get live leaderboard
  async getLeaderboard(limit = 20) {
    return this.request(`/api/game/leaderboard?limit=${limit}`, {
      method: 'GET'
    });
  }

  // Get game state status
  async getStatus() {
    return this.request('/api/game/status', {
      method: 'GET'
    });
  }
}

const Api = new ApiClient();
if (typeof module !== 'undefined' && module.exports) {
  module.exports = ApiClient;
}
