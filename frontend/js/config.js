/**
 * Game Configuration Module
 * Single place for all tuning parameters. Zero hardcoding in engine/UI!
 */

function resolveApiBaseUrl() {
  if (typeof window === 'undefined') return 'http://localhost:3000';

  // 1. Explicit global override
  if (window.__GAME_API_URL__) {
    return window.__GAME_API_URL__.replace(/\/+$/, '');
  }

  // 2. URL search parameter override (e.g. ?api=https://backend.example.com)
  try {
    const urlParams = new URLSearchParams(window.location.search);
    const queryApi = urlParams.get('api');
    if (queryApi) {
      sessionStorage.setItem('GAME_API_URL', queryApi);
      return queryApi.replace(/\/+$/, '');
    }
    const storedApi = sessionStorage.getItem('GAME_API_URL') || localStorage.getItem('GAME_API_URL');
    if (storedApi) {
      return storedApi.replace(/\/+$/, '');
    }
  } catch (e) {
    // Storage access fallback
  }

  // 3. Localhost development fallback
  if (typeof window !== 'undefined' && (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1')) {
    return 'http://localhost:8000';
  }

  // 4. Production backend default
  return 'https://backend-aarna.onrender.com';
}

const GameConfig = {
  // Game parameters: 3 mini-game types with 3 rounds each (Total 9 rounds)
  totalRounds: 9,
  pairsPerRound: 3, // 3 pairs = 6 cards per round
  mismatchDelayMs: 800,

  // Pre-existing card image assets (9 unique items for 3 rounds of 3 pairs)
  imagePool: [
    { img: "images/cards/card_1.webp", name: "Card 1" },
    { img: "images/cards/card_2.webp", name: "Card 2" },
    { img: "images/cards/card_3.webp", name: "Card 3" },
    { img: "images/cards/card_4.webp", name: "Card 4" },
    { img: "images/cards/card_5.webp", name: "Card 5" },
    { img: "images/cards/meme1.webp", name: "Meme 1" },
    { img: "images/cards/meme2.webp", name: "Meme 2" },
    { img: "images/cards/meme3.webp", name: "Meme 3" },
    { img: "images/cards/meme4.webp", name: "Meme 4" }
  ],

  // Image assets for the 3 Jigsaw rounds (Rounds 4, 5, 6)
  jigsawImages: [
    'images/puzzel.jpeg',
    'images/cards/card_1.webp',
    'images/cards/card_4.webp'
  ],

  // Image assets for the 3 Slider rounds (Rounds 7, 8, 9)
  sliderImages: [
    'images/Logo.png',
    'images/cards/card_2.webp',
    'images/cards/meme3.webp'
  ],

  // Scoring Rules
  scoring: {
    pointsPerMatch: 100,
    wrongMatchPenalty: 20,
    roundBonus: 150,
    maxSpeedBonusPerRound: 100,
    targetRoundDurationSeconds: 10
  },

  // Networking & Reliability
  api: {
    baseUrl: resolveApiBaseUrl(),
    timeoutMs: 8000,
    retryIntervalMs: 5000,
    maxQueueRetries: 10
  },

  // Method to merge dynamic config from backend
  hydrate(serverConfig) {
    if (!serverConfig) return;
    if (serverConfig.totalRounds) this.totalRounds = serverConfig.totalRounds;
    if (serverConfig.pairsPerRound) this.pairsPerRound = serverConfig.pairsPerRound;
    if (serverConfig.mismatchDelayMs) this.mismatchDelayMs = serverConfig.mismatchDelayMs;
    if (Array.isArray(serverConfig.imagePool) && serverConfig.imagePool.length >= this.pairsPerRound) {
      this.imagePool = serverConfig.imagePool;
    }
    if (serverConfig.scoring) {
      this.scoring = { ...this.scoring, ...serverConfig.scoring };
    }
  }
};

if (typeof module !== 'undefined' && module.exports) {
  module.exports = GameConfig;
}
