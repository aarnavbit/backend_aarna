/**
 * UI Renderer Module
 * Dedicated DOM manipulator subscribing to state transitions.
 * Allows visual redesign without touching game engine or network logic!
 */
class UIRenderer {
  constructor() {
    // Screen Elements
    this.screens = {
      start: document.getElementById('screen-start'),
      game: document.getElementById('screen-game'),
      result: document.getElementById('screen-result'),
      leaderboard: document.getElementById('screen-leaderboard')
    };

    // HUD Elements
    this.hudRound = document.getElementById('hud-round-text');
    this.hudScore = document.getElementById('hud-score-text');
    this.hudTimer = document.getElementById('hud-timer-text');
    this.hudPlayerName = document.getElementById('hud-player-name');
    this.roundPairsLeft = document.getElementById('round-pairs-remaining');
    this.comboBanner = document.getElementById('combo-banner');
    this.comboText = document.getElementById('combo-text');
    this.soundIcon = document.getElementById('sound-icon');

    // Grid Container
    this.cardGrid = document.getElementById('card-grid');

    // Result Elements
    this.resultPlayerName = document.getElementById('result-player-name');
    this.resultFinalScore = document.getElementById('result-final-score');
    this.resultRankBadge = document.getElementById('result-rank-badge');
    this.statTotalTime = document.getElementById('stat-total-time');
    this.statTotalMatches = document.getElementById('stat-total-matches');
    this.statSpeedBonus = document.getElementById('stat-speed-bonus');
    this.statWrongMoves = document.getElementById('stat-wrong-moves');
    this.syncStatusMsg = document.getElementById('sync-status-msg');

    // Leaderboard Elements
    this.leaderboardList = document.getElementById('leaderboard-list');
    this.offlineBadge = document.getElementById('offline-badge');

    // Lobby & Synchronized State Elements
    this.lobbyStatusBanner = document.getElementById('lobby-status-banner');
    this.lobbyStatusText = document.getElementById('lobby-status-text');
    this.lobbyReadyMsg = document.getElementById('lobby-ready-msg');
    this.btnStartText = document.getElementById('btn-start-text');
    this.gameEndedAlert = document.getElementById('game-ended-alert');
    this.resultEndedNotice = document.getElementById('result-ended-notice');

    // Toasts & Confetti
    this.toastContainer = document.getElementById('toast-container');
    this.confettiCanvas = document.getElementById('confetti-canvas');

    this.timerInterval = null;
  }

  // Switch Active Screen with Smooth Fade
  showScreen(screenName) {
    Object.keys(this.screens).forEach(name => {
      const el = this.screens[name];
      if (name === screenName) {
        el.classList.remove('screen-hidden');
        el.classList.add('screen-active');
      } else {
        el.classList.remove('screen-active');
        el.classList.add('screen-hidden');
      }
    });
  }

  // Update Live Lobby Status
  updateLobbyStatus(gameState) {
    if (!this.lobbyStatusBanner || !this.lobbyStatusText) return;

    const { status, roundNumber } = gameState || {};
    this.lobbyStatusBanner.className = 'lobby-status-banner';

    if (status === 'waiting') {
      this.lobbyStatusBanner.classList.add('status-waiting');
      this.lobbyStatusText.innerHTML = `⏳ <strong>LOBBY OPEN</strong> — Waiting for host to start game...`;
      if (this.btnStartText) this.btnStartText.textContent = 'READY / JOIN LOBBY';
    } else if (status === 'playing') {
      this.lobbyStatusBanner.classList.add('status-playing');
      this.lobbyStatusText.innerHTML = `🚀 <strong>ROUND #${roundNumber || 1} IN PROGRESS!</strong> Jump in now!`;
      if (this.btnStartText) this.btnStartText.textContent = 'START PLAYING NOW';
      if (this.lobbyReadyMsg) this.lobbyReadyMsg.classList.add('hidden');
    } else if (status === 'ended') {
      this.lobbyStatusBanner.classList.add('status-ended');
      this.lobbyStatusText.innerHTML = `🛑 <strong>ROUND #${roundNumber || 1} ENDED</strong> — Waiting for next round...`;
      if (this.btnStartText) this.btnStartText.textContent = 'WAIT FOR NEXT ROUND';
      if (this.lobbyReadyMsg) this.lobbyReadyMsg.classList.add('hidden');
    }
  }

  setPlayerReady(isReady) {
    if (this.lobbyReadyMsg) {
      this.lobbyReadyMsg.classList.toggle('hidden', !isReady);
    }
    if (this.btnStartText) {
      this.btnStartText.textContent = isReady ? '✅ READY (WAITING...)' : 'READY / JOIN LOBBY';
    }
  }

  showGameEndedAlert() {
    if (this.gameEndedAlert) {
      this.gameEndedAlert.classList.remove('hidden');
    }
  }

  hideGameEndedAlert() {
    if (this.gameEndedAlert) {
      this.gameEndedAlert.classList.add('hidden');
    }
  }

  // Toast Notification
  showToast(message, type = 'info', duration = 3000) {
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    
    const icon = type === 'success' ? '✅' : (type === 'warning' ? '⚠️' : (type === 'error' ? '❌' : 'ℹ️'));
    toast.innerHTML = `<span>${icon}</span> <span>${message}</span>`;
    
    this.toastContainer.appendChild(toast);
    setTimeout(() => {
      toast.style.opacity = '0';
      toast.style.transform = 'translateY(-20px)';
      toast.style.transition = 'all 0.3s ease';
      setTimeout(() => toast.remove(), 300);
    }, duration);
  }

  // Sound Icon Toggle
  updateSoundIcon(isMuted) {
    if (this.soundIcon) {
      this.soundIcon.textContent = isMuted ? '🔇' : '🔊';
    }
  }

  // Start HUD Timer
  startTimer(startTime) {
    if (this.timerInterval) clearInterval(this.timerInterval);
    const update = () => {
      const elapsed = Math.max(0, Math.floor((Date.now() - startTime) / 1000));
      const mins = String(Math.floor(elapsed / 60)).padStart(2, '0');
      const secs = String(elapsed % 60).padStart(2, '0');
      if (this.hudTimer) {
        this.hudTimer.textContent = `${mins}:${secs}`;
      }
    };
    update();
    this.timerInterval = setInterval(update, 1000);
  }

  stopTimer() {
    if (this.timerInterval) {
      clearInterval(this.timerInterval);
      this.timerInterval = null;
    }
  }

  // Round Intro Overlay Announcement
  showRoundAnnouncement(roundNum, title, description) {
    let overlay = document.getElementById('round-intro-overlay');
    if (!overlay) {
      overlay = document.createElement('div');
      overlay.id = 'round-intro-overlay';
      overlay.className = 'round-intro-overlay';
      document.body.appendChild(overlay);
    }
    overlay.innerHTML = `
      <div class="round-intro-card">
        <div class="round-intro-badge">STAGE ${roundNum} OF 3</div>
        <h2 class="round-intro-title">${title}</h2>
        <p class="round-intro-desc">${description}</p>
        <div class="round-intro-bar"></div>
      </div>
    `;
    overlay.classList.add('is-active');
    setTimeout(() => {
      overlay.classList.remove('is-active');
    }, 1400);
  }

  // Update HUD
  updateHUD(state) {
    if (this.hudRound) this.hudRound.textContent = `${state.round}/${state.totalRounds}`;
    if (this.hudPlayerName) this.hudPlayerName.textContent = state.playerName || 'Player';
    
    if (this.hudScore) {
      this.hudScore.textContent = state.score;
      this.hudScore.classList.remove('score-bump');
      void this.hudScore.offsetWidth; // Force reflow
      this.hudScore.classList.add('score-bump');
    }

    if (this.roundPairsLeft) {
      if (state.round === 1) {
        const pairsLeft = Math.max(0, 3 - state.matchesThisRound);
        this.roundPairsLeft.textContent = `${pairsLeft} pair${pairsLeft === 1 ? '' : 's'} left`;
      } else if (state.round === 2) {
        this.roundPairsLeft.textContent = `Jigsaw Puzzle`;
      } else if (state.round === 3) {
        this.roundPairsLeft.textContent = `15-Slider Puzzle`;
      }
    }

    // Streak / Combo
    if (state.streak > 1) {
      this.comboText.textContent = `🔥 ${state.streak}x STREAK!`;
      this.comboBanner.classList.remove('hidden');
    } else {
      this.comboBanner.classList.add('hidden');
    }
  }

  // Render Card Grid
  renderDeck(cards, onCardClick) {
    this.cardGrid.innerHTML = '';
    cards.forEach(card => {
      const cardEl = document.createElement('div');
      cardEl.className = 'card-item';
      cardEl.id = `card-${card.id}`;
      cardEl.dataset.cardId = card.id;

      // Resolve pre-existing image asset
      let imgSrc = 'images/cards/card_1.webp';
      let altText = 'Card Face';

      if (typeof card.content === 'object' && card.content !== null) {
        imgSrc = card.content.img || 'images/cards/card_1.webp';
        altText = card.content.name || 'Card Face';
      } else if (typeof card.content === 'string') {
        imgSrc = card.content;
      }

      cardEl.innerHTML = `
        <div class="card-inner">
          <div class="card-face card-face-back">
            <div class="card-back-pattern">
              <img src="images/Logo.png" alt="AARNA" class="card-back-logo" loading="eager" decoding="async" />
            </div>
          </div>
          <div class="card-face card-face-front">
            <img 
              src="${imgSrc}" 
              alt="${altText}" 
              class="card-content-img is-loaded" 
              loading="eager" 
              decoding="async"
              draggable="false"
              onerror="this.onerror=null; this.src='images/cards/card_1.webp';"
            />
          </div>
        </div>
      `;

      cardEl.addEventListener('click', () => {
        if (typeof onCardClick === 'function') {
          onCardClick(card.id);
        }
      });

      this.cardGrid.appendChild(cardEl);
    });
  }

  // Card Visual State Transitions
  flipCard(cardId) {
    const el = document.getElementById(`card-${cardId}`);
    if (el) el.classList.add('is-flipped');
  }

  setMatchedCards(cardId1, cardId2) {
    const el1 = document.getElementById(`card-${cardId1}`);
    const el2 = document.getElementById(`card-${cardId2}`);
    if (el1) {
      el1.classList.add('is-matched', 'is-disabled');
    }
    if (el2) {
      el2.classList.add('is-matched', 'is-disabled');
    }
  }

  setMismatchCards(cardId1, cardId2, onComplete) {
    const el1 = document.getElementById(`card-${cardId1}`);
    const el2 = document.getElementById(`card-${cardId2}`);
    if (el1) el1.classList.add('is-mismatch');
    if (el2) el2.classList.add('is-mismatch');

    setTimeout(() => {
      if (el1) el1.classList.remove('is-flipped', 'is-mismatch');
      if (el2) el2.classList.remove('is-flipped', 'is-mismatch');
      if (typeof onComplete === 'function') onComplete();
    }, 700);
  }

  // Render Result Screen
  renderResult(state, serverResult) {
    this.stopTimer();
    this.resultPlayerName.textContent = state.playerName;

    const totalDurationSec = Math.max(1, Math.round((state.gameEndTime - state.gameStartTime) / 1000));
    this.statTotalTime.textContent = `${totalDurationSec}s`;
    this.statTotalMatches.textContent = state.totalMatches;
    this.statWrongMoves.textContent = state.totalMismatches;

    let speedBonusTotal = 0;
    state.roundBreakdown.forEach(rb => speedBonusTotal += (rb.speedBonus || 0));
    this.statSpeedBonus.textContent = `+${speedBonusTotal}`;

    // Big score roll animation
    const targetScore = (serverResult && serverResult.finalScore !== undefined) ? serverResult.finalScore : state.score;
    this.animateScoreRoll(this.resultFinalScore, targetScore);

    // Rank Badge or Ended Notice
    if (serverResult && serverResult.roundEnded) {
      if (this.resultEndedNotice) this.resultEndedNotice.classList.remove('hidden');
      this.resultRankBadge.classList.add('hidden');
    } else if (serverResult && serverResult.rank) {
      if (this.resultEndedNotice) this.resultEndedNotice.classList.add('hidden');
      this.resultRankBadge.textContent = `Live Rank: #${serverResult.rank}`;
      this.resultRankBadge.classList.remove('hidden');
    } else {
      if (this.resultEndedNotice) this.resultEndedNotice.classList.add('hidden');
      this.resultRankBadge.classList.add('hidden');
    }

    // Trigger Confetti Celebration
    this.launchConfetti();
  }

  animateScoreRoll(element, targetValue) {
    let current = 0;
    const step = Math.max(1, Math.floor(targetValue / 30));
    const timer = setInterval(() => {
      current += step;
      if (current >= targetValue) {
        current = targetValue;
        clearInterval(timer);
      }
      element.textContent = current;
    }, 25);
  }

  // Render Leaderboard Screen
  renderLeaderboard(data, currentPlayerSessionId, isOffline = false) {
    this.offlineBadge.classList.toggle('hidden', !isOffline);
    this.leaderboardList.innerHTML = '';

    const players = data && Array.isArray(data.topPlayers) ? data.topPlayers : [];
    if (players.length === 0) {
      this.leaderboardList.innerHTML = `
        <div class="empty-leaderboard">
          <p>No scores submitted yet!</p>
          <p style="font-size: 0.8rem; margin-top: 4px;">Be the first player to set a high score!</p>
        </div>
      `;
      return;
    }

    players.forEach((p, idx) => {
      const isCurrent = p.sessionId === currentPlayerSessionId;
      const rankNum = idx + 1;
      let rankDisplay = `<span class="rank-number">${rankNum}</span>`;
      if (rankNum === 1) rankDisplay = `<span class="rank-top-1">🥇</span>`;
      if (rankNum === 2) rankDisplay = `<span class="rank-top-2">🥈</span>`;
      if (rankNum === 3) rankDisplay = `<span class="rank-top-3">🥉</span>`;

      const durationSec = Math.round((p.durationMs || 0) / 1000);
      const row = document.createElement('div');
      row.className = `leaderboard-row ${isCurrent ? 'is-current-player' : ''}`;
      row.innerHTML = `
        <div class="rank-col">${rankDisplay}</div>
        <div class="player-info-col">
          <span class="player-name-text">${p.playerName || 'Anonymous'}</span>
          <span class="player-meta-text">${p.roundsCompleted || 3} rounds • ${durationSec}s</span>
        </div>
        <div class="score-col">
          <span class="score-val-text">${p.score}</span>
          <span class="score-time-text">PTS</span>
        </div>
      `;
      this.leaderboardList.appendChild(row);
    });
  }

  // Confetti Particle Explosion
  launchConfetti() {
    const canvas = this.confettiCanvas;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    canvas.width = canvas.parentElement.clientWidth;
    canvas.height = canvas.parentElement.clientHeight;

    const particles = [];
    const colors = ['#f4795b', '#c9aef0', '#fbbf24', '#ffffff', '#3b2412', '#10b981'];

    for (let i = 0; i < 60; i++) {
      particles.push({
        x: canvas.width / 2,
        y: canvas.height / 2 + 50,
        vx: (Math.random() - 0.5) * 12,
        vy: (Math.random() - 1.2) * 12,
        size: Math.random() * 6 + 4,
        color: colors[Math.floor(Math.random() * colors.length)],
        rotation: Math.random() * 360,
        vr: (Math.random() - 0.5) * 10,
        opacity: 1
      });
    }

    let animationFrame;
    const render = () => {
      ctx.clearRect(0, 0, canvas.width, canvas.height);
      let activeCount = 0;

      particles.forEach(p => {
        p.x += p.vx;
        p.y += p.vy;
        p.vy += 0.3; // Gravity
        p.rotation += p.vr;
        p.opacity -= 0.012;

        if (p.opacity > 0) {
          activeCount++;
          ctx.save();
          ctx.translate(p.x, p.y);
          ctx.rotate((p.rotation * Math.PI) / 180);
          ctx.fillStyle = p.color;
          ctx.globalAlpha = p.opacity;
          ctx.fillRect(-p.size / 2, -p.size / 2, p.size, p.size);
          ctx.restore();
        }
      });

      if (activeCount > 0) {
        animationFrame = requestAnimationFrame(render);
      } else {
        ctx.clearRect(0, 0, canvas.width, canvas.height);
        cancelAnimationFrame(animationFrame);
      }
    };

    render();
  }
}

const UI = new UIRenderer();
if (typeof module !== 'undefined' && module.exports) {
  module.exports = UIRenderer;
}
