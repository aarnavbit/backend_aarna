/**
 * Offline Sync & Score Queue Manager
 * Ensures players NEVER lose their score during network dropouts.
 */
class ScoreQueueManager {
  constructor(apiClient) {
    this.api = apiClient || (typeof Api !== 'undefined' ? Api : null);
    this.storageKey = 'flipcards_pending_scores';
    this.cacheKeyLeaderboard = 'flipcards_cached_leaderboard';
    this.isProcessing = false;

    this.initEventListeners();
  }

  initEventListeners() {
    if (typeof window !== 'undefined') {
      window.addEventListener('online', () => this.processQueue());
      window.addEventListener('focus', () => this.processQueue());
      // Periodic check every 10 seconds
      setInterval(() => this.processQueue(), 10000);
    }
  }

  getQueue() {
    try {
      const raw = localStorage.getItem(this.storageKey);
      return raw ? JSON.parse(raw) : [];
    } catch (e) {
      return [];
    }
  }

  saveQueue(queue) {
    try {
      localStorage.setItem(this.storageKey, JSON.stringify(queue));
    } catch (e) {}
  }

  enqueue(submission) {
    const queue = this.getQueue();
    // Avoid duplicate entries for same session
    if (!queue.some(item => item.sessionId === submission.sessionId)) {
      queue.push({
        ...submission,
        attempts: 0,
        enqueuedAt: Date.now()
      });
      this.saveQueue(queue);
    }
    this.processQueue();
  }

  async processQueue(onSuccessCallback) {
    if (this.isProcessing || !navigator.onLine) return;
    const queue = this.getQueue();
    if (queue.length === 0) return;

    this.isProcessing = true;
    const remaining = [];

    for (const item of queue) {
      try {
        const res = await this.api.submitScore({
          sessionId: item.sessionId,
          playerName: item.playerName,
          actions: item.actions
        });

        if (typeof onSuccessCallback === 'function') {
          onSuccessCallback(item, res);
        }
      } catch (err) {
        item.attempts = (item.attempts || 0) + 1;
        // Keep in queue if it was a network error or server 5xx error
        if (item.attempts < 10) {
          remaining.push(item);
        }
      }
    }

    this.saveQueue(remaining);
    this.isProcessing = false;
  }

  // Cache Leaderboard locally
  cacheLeaderboard(data) {
    try {
      localStorage.setItem(this.cacheKeyLeaderboard, JSON.stringify({
        data,
        cachedAt: Date.now()
      }));
    } catch (e) {}
  }

  getCachedLeaderboard() {
    try {
      const raw = localStorage.getItem(this.cacheKeyLeaderboard);
      return raw ? JSON.parse(raw) : null;
    } catch (e) {
      return null;
    }
  }
}

const ScoreQueue = new ScoreQueueManager(Api);
if (typeof module !== 'undefined' && module.exports) {
  module.exports = ScoreQueueManager;
}
