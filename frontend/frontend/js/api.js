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
        const error = new Error(data.error || data.message || `HTTP ${response.status}`);
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
    return this.request('/api/games/start', {
      method: 'POST',
      body: JSON.stringify({ name: playerName })
    });
  }

  // Submit final score
  async submitScore(payload) {
    return this.request('/api/games/score', {
      method: 'POST',
      body: JSON.stringify(payload)
    });
  }

  // Get live leaderboard
  async getLeaderboard(limit = 20) {
    return this.request(`/api/games/leaderboard?limit=${limit}`, {
      method: 'GET'
    });
  }
}

const Api = new ApiClient();
if (typeof module !== 'undefined' && module.exports) {
  module.exports = ApiClient;
}
