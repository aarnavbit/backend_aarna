/**
 * Main Application Orchestrator
 * Connects UI, Game Engine, State, Audio, API, Offline Queue, and WebSockets.
 */
document.addEventListener('DOMContentLoaded', () => {
  const engine = new GameEngine(GameConfig);

  // Preload card images into memory immediately for zero-lag instant display
  if (Array.isArray(GameConfig.imagePool)) {
    GameConfig.imagePool.forEach(item => {
      const src = (typeof item === 'object' && item && item.img) ? item.img : (typeof item === 'string' && (item.startsWith('http') || item.startsWith('images/') || item.endsWith('.webp') || item.endsWith('.png') || item.endsWith('.jpg') || item.endsWith('.jpeg')) ? item : null);
      if (src) {
        const preloadImg = new Image();
        preloadImg.src = src;
      }
    });
  }

  // Global Synchronized State
  let currentGameState = { status: 'waiting', roundNumber: 0, startTime: null };
  let isPlayerWaitingInLobby = false;

  // Initialize Socket.io
  const socket = (typeof io !== 'undefined') ? ((GameConfig.api.baseUrl && GameConfig.api.baseUrl.startsWith('http')) ? io(GameConfig.api.baseUrl) : io()) : null;

  if (socket) {
    socket.on('connect', () => {
      console.log('[Socket] Connected to live event server.');
    });

    socket.on('game_state', (state) => {
      currentGameState = state;
      UI.updateLobbyStatus(state);
    });

    socket.on('game_started', (state) => {
      console.log('[Socket] Live Game Started:', state);
      currentGameState = state;
      UI.updateLobbyStatus(state);
      UI.hideGameEndedAlert();
      UI.showToast(`🚀 ROUND #${state.roundNumber || 1} HAS STARTED!`, 'success', 3500);

      // Auto-launch for players waiting in lobby with their name
      const rawName = nameInput.value.trim();
      if (AppState.currentScreen === 'start' && (isPlayerWaitingInLobby || rawName)) {
        handleStartGame();
      }
    });

    socket.on('game_ended', (state) => {
      console.log('[Socket] Live Game Ended:', state);
      currentGameState = state;
      UI.updateLobbyStatus(state);

      if (AppState.currentScreen === 'game') {
        UI.showGameEndedAlert();
        UI.showToast('⏳ Host ended the round! Scores will not be ranked.', 'warning', 4000);
      }
    });

    socket.on('leaderboard_update', () => {
      if (AppState.currentScreen === 'leaderboard') {
        loadLeaderboard();
      }
    });

    socket.on('leaderboard_reset', () => {
      if (AppState.currentScreen === 'leaderboard') {
        loadLeaderboard();
      }
    });
  }

  // Fetch initial game status on load
  Api.request('/api/games/status').then(res => {
    if (res && res.gameState) {
      currentGameState = res.gameState;
      UI.updateLobbyStatus(res.gameState);
    }
  }).catch(() => {});

  // Bind State to UI Renderer
  AppState.subscribe((state, event, data) => {
    if (event === 'screen_change') {
      UI.showScreen(data.screen);
    } else if (event === 'round_start') {
      UI.updateHUD(state);
      UI.startTimer(state.roundStartTime);
    } else if (event === 'card_flipped') {
      UI.flipCard(data.cardId);
      Sound.playFlip();
    } else if (event === 'match_success') {
      UI.setMatchedCards(data.cardId1, data.cardId2);
      UI.updateHUD(state);
      Sound.playMatch();
    } else if (event === 'match_fail') {
      UI.updateHUD(state);
      Sound.playMismatch();
      UI.setMismatchCards(data.cardId1, data.cardId2, () => {
        AppState.unflipCards(data.cardId1, data.cardId2);
      });
    } else if (event === 'round_complete') {
      UI.showToast(`🎉 Round ${data.round} Clear! +${data.roundBonus + data.speedBonus} pts`, 'success', 2000);
    }
  });

  // ------------------------------------------------------------------------
  // 1. Start Game Flow
  // ------------------------------------------------------------------------
  const startForm = document.getElementById('start-form');
  const nameInput = document.getElementById('player-name-input');

  async function handleStartGame() {
    const rawName = nameInput.value.trim();
    if (!rawName) {
      UI.showToast('Please enter your name to play!', 'warning');
      nameInput.focus();
      return;
    }

    // Check synchronized state
    if (currentGameState.status === 'waiting') {
      isPlayerWaitingInLobby = true;
      UI.setPlayerReady(true);
      UI.showToast('✅ Name registered! Waiting for host to start the round...', 'info', 3000);
      return;
    }

    if (currentGameState.status === 'ended') {
      UI.showToast('⚠️ This round has ended. Please wait for the host to start a new round!', 'warning', 3000);
      return;
    }

    // Status is 'playing' -> Start session
    isPlayerWaitingInLobby = false;
    UI.setPlayerReady(false);
    UI.hideGameEndedAlert();

    let sessionId = 'local_' + Math.random().toString(36).substring(2, 9);
    try {
      const serverSession = await Api.startGame(rawName);
      if (serverSession && serverSession.sessionId) {
        sessionId = serverSession.sessionId;
        if (serverSession.config) {
          GameConfig.hydrate(serverSession.config);
        }
      } else if (serverSession && serverSession.inLobby) {
        isPlayerWaitingInLobby = true;
        UI.setPlayerReady(true);
        UI.showToast(serverSession.message || 'Waiting for host...', 'info', 3000);
        return;
      }
    } catch (err) {
      console.warn('[Network] Offline session started:', err.message);
      UI.showToast('Starting offline mode. Score will sync later!', 'warning', 2500);
    }

    // Initialize App State
    AppState.initSession(sessionId, rawName, GameConfig.totalRounds);
    AppState.setScreen('game');

    // Start Round 1
    startRound(1);
  }

  startForm.addEventListener('submit', (e) => {
    e.preventDefault();
    handleStartGame();
  });

  // ------------------------------------------------------------------------
  // 2. Round Gameplay Management
  // ------------------------------------------------------------------------
  function startRound(roundNum) {
    if (currentGameState.roundNumber === 2) {
      // Round 2: Jigsaw Puzzle Mode
      if (UI.cardGrid) UI.cardGrid.classList.add('hidden');
      const jigsawBoard = document.getElementById('jigsaw-board');
      if (jigsawBoard) jigsawBoard.classList.remove('hidden');

      if (!window.jigsawGame) {
        window.jigsawGame = new JigsawEngine('jigsaw-canvas');
      }
      
      AppState.startRound(roundNum, []);
      window.jigsawGame.startPuzzle(roundNum, () => {
        // Sub-round complete
        const roundDurationMs = Date.now() - AppState.roundStartTime;
        const bonus = engine.calculateRoundBonus(roundDurationMs);
        AppState.matchesThisRound = GameConfig.pairsPerRound || 3; // Faux max matches
        AppState.totalMatches += AppState.matchesThisRound;
        AppState.recordRoundCompletion(bonus.roundBonus, bonus.speedBonus, roundDurationMs);

        setTimeout(() => {
          if (AppState.round < GameConfig.totalRounds) {
            startRound(AppState.round + 1);
          } else {
            handleGameEnd();
          }
        }, 1500);
      });
      return;
    }

    // Default: Flipcard Mode
    const jigsawBoard = document.getElementById('jigsaw-board');
    if (jigsawBoard) jigsawBoard.classList.add('hidden');
    if (UI.cardGrid) UI.cardGrid.classList.remove('hidden');

    const deck = engine.generateRoundDeck(
      roundNum,
      GameConfig.imagePool,
      GameConfig.pairsPerRound
    );

    AppState.startRound(roundNum, deck);
    UI.renderDeck(deck, handleCardClick);
  }

  function handleCardClick(cardId) {
    const result = engine.handleCardTap(cardId, AppState);
    if (!result) return;

    if (result.type === 'match') {
      if (result.isRoundComplete) {
        const roundDurationMs = Date.now() - AppState.roundStartTime;
        const bonus = engine.calculateRoundBonus(roundDurationMs);
        AppState.recordRoundCompletion(bonus.roundBonus, bonus.speedBonus, roundDurationMs);

        // Check if next round or final game over
        setTimeout(() => {
          if (AppState.round < GameConfig.totalRounds) {
            startRound(AppState.round + 1);
          } else {
            handleGameEnd();
          }
        }, 600);
      }
    }
  }

  // ------------------------------------------------------------------------
  // 3. Final Game Completion & Score Submission
  // ------------------------------------------------------------------------
  async function handleGameEnd() {
    AppState.recordGameCompletion();
    Sound.playVictory();

    const submissionPayload = {
      sessionId: AppState.sessionId,
      playerName: AppState.playerName,
      actions: {
        roundsCompleted: AppState.totalRounds,
        matches: AppState.totalMatches,
        mismatches: AppState.totalMismatches,
        durationMs: AppState.gameEndTime - AppState.gameStartTime,
        roundBreakdown: AppState.roundBreakdown
      }
    };

    let serverResult = null;
    try {
      serverResult = await Api.submitScore(submissionPayload);
      if (serverResult.roundEnded) {
        UI.syncStatusMsg.innerHTML = '<span class="sync-dot" style="background:#ef4444;"></span> Round ended by host. Score not ranked.';
        UI.showToast('Round ended before submission. Score not ranked.', 'warning', 4000);
      } else {
        UI.syncStatusMsg.innerHTML = '<span class="sync-dot"></span> Score synced to live rankings!';
      }
    } catch (err) {
      console.warn('[Score Submit] Failed online submission, queueing locally:', err.message);
      ScoreQueue.enqueue(submissionPayload);
      UI.syncStatusMsg.innerHTML = '<span class="sync-dot" style="background:#f59e0b;"></span> Saved offline. Will sync when connected!';
    }

    UI.renderResult(AppState, serverResult);
    AppState.setScreen('result');
  }

  // ------------------------------------------------------------------------
  // 4. Leaderboard Flow
  // ------------------------------------------------------------------------
  async function loadLeaderboard() {
    AppState.setScreen('leaderboard');
    UI.leaderboardList.innerHTML = '<div class="loading-spinner">Fetching live rankings...</div>';

    try {
      const data = await Api.getLeaderboard(20);
      ScoreQueue.cacheLeaderboard(data);
      UI.renderLeaderboard(data, AppState.sessionId, false);
    } catch (err) {
      console.warn('[Leaderboard] Network error, using cached copy:', err.message);
      const cached = ScoreQueue.getCachedLeaderboard();
      if (cached && cached.data) {
        UI.renderLeaderboard(cached.data, AppState.sessionId, true);
      } else {
        UI.renderLeaderboard({ topPlayers: [] }, AppState.sessionId, true);
      }
      UI.showToast('Using offline leaderboard data', 'warning', 2500);
    }
  }

  // ------------------------------------------------------------------------
  // 5. Button Listeners & Navigation
  // ------------------------------------------------------------------------
  document.getElementById('btn-view-leaderboard').addEventListener('click', loadLeaderboard);
  document.getElementById('btn-result-leaderboard').addEventListener('click', loadLeaderboard);
  document.getElementById('btn-refresh-leaderboard').addEventListener('click', loadLeaderboard);

  document.getElementById('btn-back-from-leaderboard').addEventListener('click', () => {
    if (AppState.gameEndTime > 0) {
      AppState.setScreen('result');
    } else {
      AppState.setScreen('start');
    }
  });

  document.getElementById('btn-play-again').addEventListener('click', () => {
    AppState.setScreen('start');
    nameInput.focus();
  });

  document.getElementById('btn-leaderboard-play').addEventListener('click', () => {
    AppState.setScreen('start');
    nameInput.focus();
  });

  // Sound Toggle
  document.getElementById('btn-toggle-sound').addEventListener('click', () => {
    const isAudioOn = Sound.toggleMute();
    UI.updateSoundIcon(!isAudioOn);
    UI.showToast(isAudioOn ? 'Sound On 🔊' : 'Sound Muted 🔇', 'info', 1500);
  });
});
