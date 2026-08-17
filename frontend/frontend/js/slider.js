/**
 * Lightweight Image Sliding Puzzle (15-Puzzle) - Round 3
 * Self-contained, zero-dependency, event-driven module.
 */
class SliderEngine {
  constructor(options = {}) {
    this.gridElement = document.getElementById(options.gridId || 'slider-grid');
    this.movesElement = document.getElementById(options.movesId || 'slider-moves-count');
    this.restartButton = document.getElementById(options.restartBtnId || 'btn-restart-slider');
    
    this.config = (typeof GameConfig !== 'undefined' && GameConfig.slider) 
      ? GameConfig.slider 
      : { image: 'images/Logo.png', gridSize: 4 };

    this.imgSrc = options.image || this.config.image || 'images/Logo.png';
    this.gridSize = 4;
    this.totalTiles = 16;
    this.emptyValue = 15; // Represents the empty slot
    
    this.board = []; // 16 positions, values 0..15
    this.tileElements = {}; // Map of tileId -> DOM element
    this.moves = 0;
    this.isCompleted = false;
    this.isLocked = false;
    this.onComplete = null;

    this.boundKeyDown = this.handleKeyDown.bind(this);
    this.boundRestart = this.restart.bind(this);
    
    this.initDOM();
    this.bindGlobalEvents();
  }

  initDOM() {
    if (!this.gridElement) return;
    this.gridElement.innerHTML = '';
    this.tileElements = {};

    // Create 15 visible tile elements + 1 empty tile element (hidden until solved)
    for (let tileId = 0; tileId < this.totalTiles; tileId++) {
      const tile = document.createElement('div');
      tile.className = `slider-tile ${tileId === this.emptyValue ? 'slider-tile-empty' : ''}`;
      tile.dataset.tileId = tileId;

      const origRow = Math.floor(tileId / this.gridSize);
      const origCol = tileId % this.gridSize;

      // Slice image using background positioning across 4x4
      // 0% -> col 0, 33.333% -> col 1, 66.667% -> col 2, 100% -> col 3
      const posX = (origCol / (this.gridSize - 1)) * 100;
      const posY = (origRow / (this.gridSize - 1)) * 100;

      tile.style.backgroundImage = `url("${this.imgSrc}")`;
      tile.style.backgroundSize = `${this.gridSize * 100}% ${this.gridSize * 100}%`;
      tile.style.backgroundPosition = `${posX}% ${posY}%`;

      if (tileId !== this.emptyValue) {
        tile.addEventListener('click', () => this.handleTileClick(tileId));
        tile.addEventListener('touchstart', (e) => {
          e.preventDefault();
          this.handleTileClick(tileId);
        }, { passive: false });
      }

      this.gridElement.appendChild(tile);
      this.tileElements[tileId] = tile;
    }
  }

  bindGlobalEvents() {
    window.addEventListener('keydown', this.boundKeyDown);
    if (this.restartButton) {
      this.restartButton.addEventListener('click', this.boundRestart);
    }
  }

  unbindGlobalEvents() {
    window.removeEventListener('keydown', this.boundKeyDown);
    if (this.restartButton) {
      this.restartButton.removeEventListener('click', this.boundRestart);
    }
  }

  startPuzzle(onComplete) {
    this.onComplete = onComplete;
    this.isCompleted = false;
    this.isLocked = false;
    this.moves = 0;
    this.updateMovesDisplay();

    // Hide the 16th tile during gameplay
    if (this.tileElements[this.emptyValue]) {
      this.tileElements[this.emptyValue].classList.remove('slider-tile-revealed');
      this.tileElements[this.emptyValue].classList.add('slider-tile-empty');
    }

    this.shuffle();
  }

  /**
   * Generates a 100% guaranteed solvable in-memory shuffled state.
   * Begins from solved state and performs legal random moves.
   */
  shuffle() {
    // Solved state: [0, 1, 2, ..., 15]
    this.board = Array.from({ length: this.totalTiles }, (_, i) => i);
    let emptyPos = this.emptyValue; // index 15
    let lastMovedPos = -1;

    const shuffleSteps = 160;
    for (let step = 0; step < shuffleSteps; step++) {
      const neighbors = this.getAdjacentPositions(emptyPos);
      // Filter out the position we just moved from to avoid simple A-B-A oscillations
      const validNeighbors = neighbors.filter(pos => pos !== lastMovedPos);
      const chosenPos = validNeighbors.length > 0
        ? validNeighbors[Math.floor(Math.random() * validNeighbors.length)]
        : neighbors[Math.floor(Math.random() * neighbors.length)];

      // Swap
      this.board[emptyPos] = this.board[chosenPos];
      this.board[chosenPos] = this.emptyValue;
      lastMovedPos = emptyPos;
      emptyPos = chosenPos;
    }

    // Ensure it's not solved by accidental symmetry
    if (this.isSolved()) {
      const neighbors = this.getAdjacentPositions(emptyPos);
      const chosenPos = neighbors[0];
      this.board[emptyPos] = this.board[chosenPos];
      this.board[chosenPos] = this.emptyValue;
    }

    this.moves = 0;
    this.updateMovesDisplay();
    this.updateTilePositionsDOM(false);
  }

  getAdjacentPositions(pos) {
    const row = Math.floor(pos / this.gridSize);
    const col = pos % this.gridSize;
    const neighbors = [];

    if (row > 0) neighbors.push(pos - this.gridSize); // Up
    if (row < this.gridSize - 1) neighbors.push(pos + this.gridSize); // Down
    if (col > 0) neighbors.push(pos - 1); // Left
    if (col < this.gridSize - 1) neighbors.push(pos + 1); // Right

    return neighbors;
  }

  handleTileClick(tileId) {
    if (this.isCompleted || this.isLocked) return;

    const currentPos = this.board.indexOf(tileId);
    if (currentPos === -1) return;

    const emptyPos = this.board.indexOf(this.emptyValue);
    if (this.isAdjacent(currentPos, emptyPos)) {
      this.executeMove(currentPos, emptyPos);
    }
  }

  handleKeyDown(e) {
    if (this.isCompleted || this.isLocked) return;

    const emptyPos = this.board.indexOf(this.emptyValue);
    if (emptyPos === -1) return;

    const emptyRow = Math.floor(emptyPos / this.gridSize);
    const emptyCol = emptyPos % this.gridSize;
    let targetPos = -1;

    switch (e.key) {
      case 'ArrowUp':
        // Move tile BELOW empty slot UP into empty slot
        if (emptyRow < this.gridSize - 1) targetPos = emptyPos + this.gridSize;
        break;
      case 'ArrowDown':
        // Move tile ABOVE empty slot DOWN into empty slot
        if (emptyRow > 0) targetPos = emptyPos - this.gridSize;
        break;
      case 'ArrowLeft':
        // Move tile to the RIGHT of empty slot LEFT into empty slot
        if (emptyCol < this.gridSize - 1) targetPos = emptyPos + 1;
        break;
      case 'ArrowRight':
        // Move tile to the LEFT of empty slot RIGHT into empty slot
        if (emptyCol > 0) targetPos = emptyPos - 1;
        break;
      default:
        return;
    }

    if (targetPos !== -1) {
      e.preventDefault();
      this.executeMove(targetPos, emptyPos);
    }
  }

  isAdjacent(posA, posB) {
    const rowA = Math.floor(posA / this.gridSize);
    const colA = posA % this.gridSize;
    const rowB = Math.floor(posB / this.gridSize);
    const colB = posB % this.gridSize;

    const rowDiff = Math.abs(rowA - rowB);
    const colDiff = Math.abs(colA - colB);

    return (rowDiff === 1 && colDiff === 0) || (rowDiff === 0 && colDiff === 1);
  }

  executeMove(fromPos, toEmptyPos) {
    // Swap in board array
    const movedTileId = this.board[fromPos];
    this.board[toEmptyPos] = movedTileId;
    this.board[fromPos] = this.emptyValue;

    // Increment move count
    this.moves += 1;
    this.updateMovesDisplay();

    // Sound effect
    if (typeof Sound !== 'undefined' && Sound.playFlip) {
      Sound.playFlip();
    }

    // Update DOM
    this.updateTilePositionsDOM(true);

    // Check completion
    if (this.isSolved()) {
      this.handleSolved();
    }
  }

  updateTilePositionsDOM(animate = true) {
    for (let pos = 0; pos < this.totalTiles; pos++) {
      const tileId = this.board[pos];
      const el = this.tileElements[tileId];
      if (!el) continue;

      const row = Math.floor(pos / this.gridSize);
      const col = pos % this.gridSize;

      // Position using percentage offsets
      el.style.left = `calc(${col * 25}% + 3px)`;
      el.style.top = `calc(${row * 25}% + 3px)`;
      
      if (!animate) {
        el.style.transition = 'none';
        void el.offsetWidth; // Trigger reflow
        el.style.transition = '';
      }
    }
  }

  updateMovesDisplay() {
    if (this.movesElement) {
      this.movesElement.textContent = this.moves;
    }
  }

  isSolved() {
    for (let i = 0; i < this.totalTiles; i++) {
      if (this.board[i] !== i) return false;
    }
    return true;
  }

  handleSolved() {
    if (this.isCompleted) return;
    this.isCompleted = true;
    this.isLocked = true;

    // Reveal the final missing piece (16th tile) to complete the image seamlessly
    const emptyTile = this.tileElements[this.emptyValue];
    if (emptyTile) {
      emptyTile.classList.remove('slider-tile-empty');
      emptyTile.classList.add('slider-tile-revealed');
    }

    if (typeof Sound !== 'undefined' && Sound.playVictory) {
      Sound.playVictory();
    }

    if (typeof this.onComplete === 'function') {
      // Small timeout for user to see completed picture
      setTimeout(() => {
        this.onComplete({
          moves: this.moves,
          solved: true
        });
      }, 1200);
    }
  }

  restart() {
    if (this.isLocked && !this.isCompleted) return;
    this.startPuzzle(this.onComplete);
  }

  destroy() {
    this.unbindGlobalEvents();
    if (this.gridElement) {
      this.gridElement.innerHTML = '';
    }
  }
}

if (typeof module !== 'undefined' && module.exports) {
  module.exports = SliderEngine;
}
