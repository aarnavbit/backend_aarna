/**
 * 15-Puzzle Image Slider Game Module
 * Self-contained module slicing a single image into a 4x4 sliding grid.
 */
class SliderEngine {
  constructor(containerId = 'slider-board', imgSrc = 'images/Logo.png') {
    this.container = document.getElementById(containerId);
    this.imgSrc = imgSrc;
    this.gridSize = 4;
    this.totalTiles = 16;
    
    // Board state: array of 16 integers (0 to 15), where 15 is the empty slot
    this.board = Array.from({ length: 16 }, (_, i) => i);
    this.emptyIdx = 15;
    this.moves = 0;
    this.isWon = false;
    this.isShuffling = false;
    this.onComplete = null;

    // DOM Elements
    this.tileElements = [];
    this.movesDisplay = null;
    this.restartBtn = null;
    this.tray = null;
    this.fullImageOverlay = null;

    this.initDOM();
    this.bindEvents();
  }

  /**
   * Initializes the DOM structure inside the container.
   */
  initDOM() {
    if (!this.container) return;

    this.container.innerHTML = `
      <div class="slider-header-bar">
        <div class="slider-stat-pill">
          <span class="slider-stat-label">MOVES</span>
          <span id="slider-moves-count" class="slider-stat-value">0</span>
        </div>
        <button id="slider-restart-btn" class="slider-btn-restart" type="button" aria-label="Restart Puzzle">
          <span>🔄 Restart</span>
        </button>
      </div>
      <div class="slider-board-wrapper">
        <div class="slider-wood-frame">
          <div class="slider-inner-tray" id="slider-inner-tray" role="grid" aria-label="15 Puzzle Grid">
            <!-- 15 playable tiles + 1 final 16th reveal tile injected here -->
          </div>
        </div>
      </div>
    `;

    this.movesDisplay = this.container.querySelector('#slider-moves-count');
    this.restartBtn = this.container.querySelector('#slider-restart-btn');
    this.tray = this.container.querySelector('#slider-inner-tray');

    // Create 16 tile elements (0-14 visible, 15 complete 16th reveal tile)
    this.tileElements = [];
    for (let i = 0; i < 16; i++) {
      const tile = document.createElement('div');
      tile.className = `slider-tile ${i === 15 ? 'slider-tile-final' : ''}`;
      tile.setAttribute('data-tile-val', i);
      tile.setAttribute('role', 'button');
      tile.setAttribute('tabindex', '0');
      tile.setAttribute('aria-label', `Tile ${i + 1}`);

      // Calculate original correct background position
      const origRow = Math.floor(i / this.gridSize);
      const origCol = i % this.gridSize;
      const bgX = (origCol / (this.gridSize - 1)) * 100;
      const bgY = (origRow / (this.gridSize - 1)) * 100;

      tile.style.backgroundImage = `url('${this.imgSrc}')`;
      tile.style.backgroundSize = '400% 400%';
      tile.style.backgroundPosition = `${bgX}% ${bgY}%`;

      // Set initial position
      tile.style.top = `${origRow * 25}%`;
      tile.style.left = `${origCol * 25}%`;

      // Number badge for readability
      const badge = document.createElement('span');
      badge.className = 'tile-badge';
      badge.textContent = i + 1;
      tile.appendChild(badge);

      this.tray.appendChild(tile);
      this.tileElements.push(tile);
    }
  }

  /**
   * Updates background image asset for all tiles.
   */
  setImage(imgSrc) {
    if (!imgSrc) return;
    this.imgSrc = imgSrc;
    if (this.tileElements) {
      this.tileElements.forEach(tile => {
        tile.style.backgroundImage = `url('${imgSrc}')`;
      });
    }
  }

  /**
   * Starts a new puzzle game session.
   */
  startPuzzle(roundNum, onComplete, imgSrc = null) {
    this.onComplete = onComplete;
    if (imgSrc) {
      this.setImage(imgSrc);
    }
    this.resetGame();
  }

  /**
   * Resets and re-shuffles the puzzle board.
   */
  resetGame() {
    this.moves = 0;
    this.isWon = false;
    this.updateMovesDisplay();

    if (this.container) {
      this.container.classList.remove('slider-won');
    }

    // Hide final 16th tile
    const finalTile = this.tileElements[15];
    if (finalTile) {
      finalTile.classList.remove('revealed');
    }

    // Reset array to solved state
    this.board = Array.from({ length: 16 }, (_, i) => i);
    this.emptyIdx = 15;

    // Apply solvable shuffle
    this.shuffle(160);
  }

  /**
   * Generates a guaranteed solvable board using 160 random valid sliding moves.
   */
  shuffle(steps = 160) {
    this.isShuffling = true;
    let lastMovedIdx = -1;

    for (let s = 0; s < steps; s++) {
      const neighbors = this.getAdjacentIndices(this.emptyIdx);
      // Avoid immediately reversing the previous move
      const validChoices = neighbors.filter(idx => idx !== lastMovedIdx);
      const chosenIdx = validChoices.length > 0
        ? validChoices[Math.floor(Math.random() * validChoices.length)]
        : neighbors[Math.floor(Math.random() * neighbors.length)];

      // Swap in array
      this.board[this.emptyIdx] = this.board[chosenIdx];
      this.board[chosenIdx] = 15;

      lastMovedIdx = this.emptyIdx;
      this.emptyIdx = chosenIdx;
    }

    // If accidentally solved after 160 moves, make 4 extra random moves
    if (this.checkWin()) {
      const neighbors = this.getAdjacentIndices(this.emptyIdx);
      const chosenIdx = neighbors[0];
      this.board[this.emptyIdx] = this.board[chosenIdx];
      this.board[chosenIdx] = 15;
      this.emptyIdx = chosenIdx;
    }

    // Temporarily disable transitions during initial position setup
    if (this.tray) {
      this.tray.classList.add('no-animation');
    }

    this.syncDOMPositions();

    // Re-enable smooth sliding transitions
    setTimeout(() => {
      if (this.tray) {
        this.tray.classList.remove('no-animation');
      }
      this.isShuffling = false;
    }, 50);
  }

  /**
   * Synchronizes visual CSS top/left of all tiles based on board state.
   */
  syncDOMPositions() {
    for (let slotIdx = 0; slotIdx < 16; slotIdx++) {
      const tileVal = this.board[slotIdx];
      if (tileVal !== 15) {
        const row = Math.floor(slotIdx / this.gridSize);
        const col = slotIdx % this.gridSize;
        const tileEl = this.tileElements[tileVal];
        if (tileEl) {
          tileEl.style.top = `${row * 25}%`;
          tileEl.style.left = `${col * 25}%`;
        }
      }
    }
  }

  /**
   * Returns adjacent indices (Up, Down, Left, Right) for a given slot.
   */
  getAdjacentIndices(idx) {
    const row = Math.floor(idx / this.gridSize);
    const col = idx % this.gridSize;
    const neighbors = [];

    if (row > 0) neighbors.push(idx - this.gridSize); // Up
    if (row < this.gridSize - 1) neighbors.push(idx + this.gridSize); // Down
    if (col > 0) neighbors.push(idx - 1); // Left
    if (col < this.gridSize - 1) neighbors.push(idx + 1); // Right

    return neighbors;
  }

  /**
   * Handles tile movement if adjacent to the empty slot.
   */
  tryMove(tileIdx) {
    if (this.isWon || this.isShuffling) return false;

    const emptyRow = Math.floor(this.emptyIdx / this.gridSize);
    const emptyCol = this.emptyIdx % this.gridSize;
    const tileRow = Math.floor(tileIdx / this.gridSize);
    const tileCol = tileIdx % this.gridSize;

    // Movement Rule: must be strictly adjacent (Manhattan distance === 1)
    const isAdjacent = Math.abs(emptyRow - tileRow) + Math.abs(emptyCol - tileCol) === 1;
    if (!isAdjacent) return false;

    // Swap in state array
    const tileVal = this.board[tileIdx];
    this.board[this.emptyIdx] = tileVal;
    this.board[tileIdx] = 15;

    // Animate moving tile to empty slot coordinates
    const tileEl = this.tileElements[tileVal];
    if (tileEl) {
      tileEl.style.top = `${emptyRow * 25}%`;
      tileEl.style.left = `${emptyCol * 25}%`;
    }

    // Update empty slot index
    this.emptyIdx = tileIdx;

    // Increment and update moves
    this.moves++;
    this.updateMovesDisplay();

    // Play slide audio feedback
    if (typeof Sound !== 'undefined' && Sound.playFlip) {
      Sound.playFlip();
    }

    // Win verification
    if (this.checkWin()) {
      this.handleVictory();
    }

    return true;
  }

  /**
   * Verifies if all tiles are in their solved positions.
   */
  checkWin() {
    return this.board.every((val, idx) => val === idx);
  }

  /**
   * Handles win state: reveals final 16th tile, plays sound, triggers completion.
   */
  handleVictory() {
    this.isWon = true;

    if (this.container) {
      this.container.classList.add('slider-won');
    }

    // Fade in the complete 16th tile to reveal the full image
    const finalTile = this.tileElements[15];
    if (finalTile) {
      finalTile.style.top = '75%';
      finalTile.style.left = '75%';
      finalTile.classList.add('revealed');
    }

    // Sound effect
    if (typeof Sound !== 'undefined' && Sound.playVictory) {
      Sound.playVictory();
    }

    if (typeof UI !== 'undefined' && UI.showToast) {
      UI.showToast('🏆 15-Puzzle Solved!', 'success', 2500);
    }

    // Complete callback for round progression
    if (typeof this.onComplete === 'function') {
      setTimeout(() => {
        this.onComplete(this.moves);
      }, 1500);
    }
  }

  /**
   * Updates HUD moves count display.
   */
  updateMovesDisplay() {
    if (this.movesDisplay) {
      this.movesDisplay.textContent = this.moves;
    }
  }

  /**
   * Event bindings for Mouse, Touch, Keyboard and Buttons.
   */
  bindEvents() {
    // Restart Button
    if (this.restartBtn) {
      this.restartBtn.addEventListener('click', () => {
        this.resetGame();
      });
    }

    // Event Delegation for Tile Click / Tap
    if (this.tray) {
      this.tray.addEventListener('click', (e) => {
        const tile = e.target.closest('.slider-tile');
        if (!tile || tile.classList.contains('slider-tile-final')) return;

        const tileVal = parseInt(tile.getAttribute('data-tile-val'), 10);
        const tileIdx = this.board.indexOf(tileVal);
        if (tileIdx !== -1) {
          this.tryMove(tileIdx);
        }
      });
    }

    // Keyboard Arrow Controls (Physical direction pushes tile into empty slot)
    window.addEventListener('keydown', (e) => {
      if (this.isWon || this.isShuffling) return;
      if (!this.container || this.container.classList.contains('hidden')) return;

      const emptyRow = Math.floor(this.emptyIdx / this.gridSize);
      const emptyCol = this.emptyIdx % this.gridSize;

      let targetIdx = -1;

      switch (e.key) {
        case 'ArrowUp':
        case 'KeyW':
        case 'w':
        case 'W':
          // Move tile BELOW empty slot UP into empty slot
          if (emptyRow < this.gridSize - 1) {
            targetIdx = this.emptyIdx + this.gridSize;
          }
          break;
        case 'ArrowDown':
        case 'KeyS':
        case 's':
        case 'S':
          // Move tile ABOVE empty slot DOWN into empty slot
          if (emptyRow > 0) {
            targetIdx = this.emptyIdx - this.gridSize;
          }
          break;
        case 'ArrowLeft':
        case 'KeyA':
        case 'a':
        case 'A':
          // Move tile RIGHT of empty slot LEFT into empty slot
          if (emptyCol < this.gridSize - 1) {
            targetIdx = this.emptyIdx + 1;
          }
          break;
        case 'ArrowRight':
        case 'KeyD':
        case 'd':
        case 'D':
          // Move tile LEFT of empty slot RIGHT into empty slot
          if (emptyCol > 0) {
            targetIdx = this.emptyIdx - 1;
          }
          break;
      }

      if (targetIdx !== -1) {
        e.preventDefault();
        this.tryMove(targetIdx);
      }
    });
  }
}
