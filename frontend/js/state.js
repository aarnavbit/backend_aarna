/**
 * Central State Management
 * Single source of truth for application and game runtime state.
 */
class StateStore {
  constructor() {
    this.subscribers = new Set();
    this.reset();
  }

  reset() {
    this.currentScreen = 'start'; // 'start' | 'game' | 'result' | 'leaderboard'
    this.sessionId = null;
    this.playerName = '';

    // Game runtime
    this.round = 1;
    this.totalRounds = 3;
    this.score = 0;
    this.streak = 0;
    this.isLocked = false;

    // Active deck for current round
    this.cards = []; // Array of { id, pairId, content, isFlipped, isMatched }
    this.flippedCardIds = [];

    // Timing & Statistics
    this.gameStartTime = 0;
    this.gameEndTime = 0;
    this.roundStartTime = 0;
    this.roundBreakdown = []; // Array of { roundNumber, durationMs, matches, mismatches }
    this.matchesThisRound = 0;
    this.totalMatches = 0;
    this.totalMismatches = 0;

    // Leaderboard & sync state
    this.serverRank = null;
    this.isSyncing = false;
    this.isOffline = false;
  }

  // Subscribe to state changes
  subscribe(callback) {
    this.subscribers.add(callback);
    return () => this.subscribers.delete(callback);
  }

  // Notify all subscribers
  notify(eventName, data = {}) {
    for (const sub of this.subscribers) {
      try {
        sub(this, eventName, data);
      } catch (err) {
        console.error('[State Store notification error]:', err);
      }
    }
  }

  // State transitions
  setScreen(screenName) {
    this.currentScreen = screenName;
    this.notify('screen_change', { screen: screenName });
  }

  initSession(sessionId, playerName, totalRounds) {
    this.sessionId = sessionId;
    this.playerName = playerName;
    this.totalRounds = totalRounds || 3;
    this.round = 1;
    this.score = 0;
    this.streak = 0;
    this.totalMatches = 0;
    this.totalMismatches = 0;
    this.roundBreakdown = [];
    this.gameStartTime = Date.now();
    this.notify('session_init');
  }

  startRound(roundNumber, cards) {
    this.round = roundNumber;
    this.cards = cards;
    this.flippedCardIds = [];
    this.matchesThisRound = 0;
    this.isLocked = false;
    this.roundStartTime = Date.now();
    this.notify('round_start', { round: roundNumber });
  }

  flipCard(cardId) {
    const card = this.cards.find(c => c.id === cardId);
    if (!card || card.isFlipped || card.isMatched || this.isLocked) return false;

    card.isFlipped = true;
    this.flippedCardIds.push(cardId);
    this.notify('card_flipped', { cardId, card });
    return true;
  }

  setMatched(cardId1, cardId2, pointsEarned) {
    const c1 = this.cards.find(c => c.id === cardId1);
    const c2 = this.cards.find(c => c.id === cardId2);
    if (c1) c1.isMatched = true;
    if (c2) c2.isMatched = true;

    this.flippedCardIds = [];
    this.matchesThisRound++;
    this.totalMatches++;
    this.streak++;
    this.score += pointsEarned;

    this.notify('match_success', {
      cardId1,
      cardId2,
      pointsEarned,
      streak: this.streak,
      matchesThisRound: this.matchesThisRound
    });
  }

  setMismatch(cardId1, cardId2, penalty) {
    this.streak = 0;
    this.totalMismatches++;
    this.score = Math.max(0, this.score - penalty);

    this.notify('match_fail', {
      cardId1,
      cardId2,
      penalty
    });
  }

  unflipCards(cardId1, cardId2) {
    const c1 = this.cards.find(c => c.id === cardId1);
    const c2 = this.cards.find(c => c.id === cardId2);
    if (c1 && !c1.isMatched) c1.isFlipped = false;
    if (c2 && !c2.isMatched) c2.isFlipped = false;

    this.flippedCardIds = [];
    this.isLocked = false;
    this.notify('cards_unflipped', { cardId1, cardId2 });
  }

  recordRoundCompletion(roundBonus, speedBonus, roundDurationMs) {
    this.score += (roundBonus + speedBonus);
    this.roundBreakdown.push({
      roundNumber: this.round,
      durationMs: roundDurationMs,
      matches: this.matchesThisRound,
      roundBonus,
      speedBonus
    });

    this.notify('round_complete', {
      round: this.round,
      roundBonus,
      speedBonus,
      durationMs: roundDurationMs
    });
  }

  recordGameCompletion() {
    this.gameEndTime = Date.now();
    this.notify('game_complete', {
      totalTimeMs: this.gameEndTime - this.gameStartTime,
      finalScore: this.score,
      totalMatches: this.totalMatches,
      totalMismatches: this.totalMismatches
    });
  }
}

const AppState = new StateStore();
if (typeof module !== 'undefined' && module.exports) {
  module.exports = StateStore;
}
