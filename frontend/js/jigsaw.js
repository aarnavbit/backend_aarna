class JigsawEngine {
  constructor(canvasId) {
    this.canvas = document.getElementById(canvasId);
    this.ctx = this.canvas.getContext('2d');
    this.imgSrc = 'images/puzzel.jpeg';
    this.rows = 3;
    this.cols = 4;
    
    this.boardW = 0;
    this.boardH = 0;
    this.w = 0;
    this.h = 0;
    this.pieces = [];
    this.slots = [];
    this.tray = [];
    
    this.isDragging = false;
    this.draggedPiece = null;
    this.dragOffsetX = 0;
    this.dragOffsetY = 0;
    
    this.onComplete = null;
    this.img = new Image();
    this.isLoaded = false;
    
    this.bindEvents();
    
    window.addEventListener('resize', () => {
      if (this.canvas.style.display === 'block') {
        this.render(); // Adjust canvas rendering
      }
    });
  }

  startPuzzle(roundNum, onComplete, imgSrc = null) {
    this.onComplete = onComplete;
    if (imgSrc) {
      this.imgSrc = imgSrc;
    }
    this.pieces = [];
    this.slots = [];
    this.tray = [];
    this.canvas.style.display = 'block';

    const onImageReady = () => {
      this.isLoaded = true;
      this.initGame();
    };

    this.img = new Image();
    this.img.onload = onImageReady;
    this.img.onerror = () => {
      if (this.imgSrc !== 'images/Logo.png') {
        this.imgSrc = 'images/Logo.png';
        this.img.src = 'images/Logo.png';
        this.img.onload = onImageReady;
      }
    };
    this.img.src = this.imgSrc;
  }

  initGame() {
    this.resizeCanvas();
    this.w = this.boardW / this.cols;
    this.h = this.boardH / this.rows;

    this.generateEdges();
    this.createPieces();
    this.shuffleToTray();
    this.createSlots();
    this.render();
  }

  resizeCanvas() {
    const parent = this.canvas.parentElement;
    const availW = parent.clientWidth || 360;
    const availH = (parent.clientHeight && parent.clientHeight > 200) ? parent.clientHeight : 520;
    
    this.canvas.width = Math.min(availW, 460);
    this.canvas.height = availH;
    
    // Fit board to aspect ratio
    const imgAspect = (this.img.naturalWidth && this.img.naturalHeight) 
      ? (this.img.naturalWidth / this.img.naturalHeight) 
      : 1.33;
    const maxBoardW = this.canvas.width * 0.92;
    const maxBoardH = this.canvas.height * 0.50; 

    if (maxBoardW / maxBoardH > imgAspect) {
      this.boardH = maxBoardH;
      this.boardW = maxBoardH * imgAspect;
    } else {
      this.boardW = maxBoardW;
      this.boardH = maxBoardW / imgAspect;
    }
    
    this.boardX = (this.canvas.width - this.boardW) / 2;
    this.boardY = 12;
  }

  generateEdges() {
    this.hEdges = [];
    for(let r = 0; r < this.rows - 1; r++) {
      let row = [];
      for(let c = 0; c < this.cols; c++) {
        row.push(Math.random() > 0.5 ? 1 : -1);
      }
      this.hEdges.push(row);
    }
    
    this.vEdges = [];
    for(let r = 0; r < this.rows; r++) {
      let row = [];
      for(let c = 0; c < this.cols - 1; c++) {
        row.push(Math.random() > 0.5 ? 1 : -1);
      }
      this.vEdges.push(row);
    }
  }

  createPieces() {
    for (let r = 0; r < this.rows; r++) {
      for (let c = 0; c < this.cols; c++) {
        const top = r === 0 ? 0 : -this.hEdges[r-1][c];
        const right = c === this.cols - 1 ? 0 : this.vEdges[r][c];
        const bottom = r === this.rows - 1 ? 0 : this.hEdges[r][c];
        const left = c === 0 ? 0 : -this.vEdges[r][c-1];
        
        const padding = Math.max(this.w, this.h) * 0.3;
        const pCanvas = document.createElement('canvas');
        pCanvas.width = Math.ceil(this.w + padding * 2);
        pCanvas.height = Math.ceil(this.h + padding * 2);
        const pCtx = pCanvas.getContext('2d');
        
        // Draw path
        this.drawPiecePath(pCtx, padding, padding, this.w, this.h, top, right, bottom, left);
        pCtx.clip();
        
        // Draw image slice with safe bounds clamping
        const sx = c * (this.img.width / this.cols);
        const sy = r * (this.img.height / this.rows);
        const sw = this.img.width / this.cols;
        const sh = this.img.height / this.rows;
        
        const padRatioW = padding / this.w;
        const padRatioH = padding / this.h;
        const srcSx = sx - (sw * padRatioW);
        const srcSy = sy - (sh * padRatioH);
        const srcSw = sw + (sw * padRatioW * 2);
        const srcSh = sh + (sh * padRatioH * 2);

        const clampedSrcX = Math.max(0, srcSx);
        const clampedSrcY = Math.max(0, srcSy);
        const clampedSrcMaxX = Math.min(this.img.width, srcSx + srcSw);
        const clampedSrcMaxY = Math.min(this.img.height, srcSy + srcSh);
        const clampedSrcW = Math.max(0, clampedSrcMaxX - clampedSrcX);
        const clampedSrcH = Math.max(0, clampedSrcMaxY - clampedSrcY);

        const destX = ((clampedSrcX - srcSx) / srcSw) * pCanvas.width;
        const destY = ((clampedSrcY - srcSy) / srcSh) * pCanvas.height;
        const destW = (clampedSrcW / srcSw) * pCanvas.width;
        const destH = (clampedSrcH / srcSh) * pCanvas.height;

        if (clampedSrcW > 0 && clampedSrcH > 0) {
          pCtx.drawImage(this.img, clampedSrcX, clampedSrcY, clampedSrcW, clampedSrcH, destX, destY, destW, destH);
        }
        
        // Outline
        pCtx.lineWidth = 2.5;
        pCtx.strokeStyle = '#3b2412';
        this.drawPiecePath(pCtx, padding, padding, this.w, this.h, top, right, bottom, left);
        pCtx.stroke();

        this.pieces.push({
          id: `p_${r}_${c}`,
          r, c,
          canvas: pCanvas,
          padding,
          x: 0, y: 0,
          targetR: r, targetC: c,
          currentSlot: null
        });
      }
    }
  }

  drawPiecePath(ctx, x, y, w, h, top, right, bottom, left) {
    ctx.beginPath();
    ctx.moveTo(x, y);
    const tw = w * 0.2;
    const th = h * 0.2;

    // Top
    if (top === 0) ctx.lineTo(x + w, y);
    else {
      ctx.lineTo(x + w/2 - tw, y);
      ctx.bezierCurveTo(x + w/2 - tw, y - top*th*2, x + w/2 + tw, y - top*th*2, x + w/2 + tw, y);
      ctx.lineTo(x + w, y);
    }
    
    // Right
    if (right === 0) ctx.lineTo(x + w, y + h);
    else {
      ctx.lineTo(x + w, y + h/2 - th);
      ctx.bezierCurveTo(x + w + right*tw*2, y + h/2 - th, x + w + right*tw*2, y + h/2 + th, x + w, y + h/2 + th);
      ctx.lineTo(x + w, y + h);
    }
    
    // Bottom
    if (bottom === 0) ctx.lineTo(x, y + h);
    else {
      ctx.lineTo(x + w/2 + tw, y + h);
      ctx.bezierCurveTo(x + w/2 + tw, y + h + bottom*th*2, x + w/2 - tw, y + h + bottom*th*2, x + w/2 - tw, y + h);
      ctx.lineTo(x, y + h);
    }
    
    // Left
    if (left === 0) ctx.lineTo(x, y);
    else {
      ctx.lineTo(x, y + h/2 + th);
      ctx.bezierCurveTo(x - left*tw*2, y + h/2 + th, x - left*tw*2, y + h/2 - th, x, y + h/2 - th);
      ctx.lineTo(x, y);
    }
  }

  shuffleToTray() {
    const trayY = this.boardY + this.boardH + 20;
    const trayH = this.canvas.height - trayY - 20;
    
    for (let i = this.pieces.length - 1; i > 0; i--) {
      const j = Math.floor(Math.random() * (i + 1));
      [this.pieces[i], this.pieces[j]] = [this.pieces[j], this.pieces[i]];
    }

    this.pieces.forEach((p) => {
      p.currentSlot = null;
      p.x = Math.random() * (this.canvas.width - this.w) + this.w/2;
      p.y = trayY + Math.random() * (trayH - this.h) + this.h/2;
    });
  }

  createSlots() {
    this.slots = [];
    for (let r = 0; r < this.rows; r++) {
      for (let c = 0; c < this.cols; c++) {
        this.slots.push({
          r, c,
          x: this.boardX + c * this.w + this.w/2,
          y: this.boardY + r * this.h + this.h/2,
          piece: null
        });
      }
    }
  }

  render() {
    this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);
    
    // Draw board background
    this.ctx.fillStyle = '#fbeee0';
    this.ctx.shadowColor = '#3b2412';
    this.ctx.shadowBlur = 0;
    this.ctx.shadowOffsetX = 4;
    this.ctx.shadowOffsetY = 4;
    this.ctx.fillRect(this.boardX, this.boardY, this.boardW, this.boardH);
    this.ctx.strokeStyle = '#3b2412';
    this.ctx.lineWidth = 2.5;
    this.ctx.strokeRect(this.boardX, this.boardY, this.boardW, this.boardH);
    this.ctx.shadowOffsetX = 0;
    this.ctx.shadowOffsetY = 0;

    // Draw slot outlines
    this.ctx.strokeStyle = 'rgba(59, 36, 18, 0.2)';
    this.ctx.lineWidth = 1;
    this.slots.forEach(s => {
      this.ctx.strokeRect(s.x - this.w/2, s.y - this.h/2, this.w, this.h);
    });

    // Draw tray divider
    const trayY = this.boardY + this.boardH + 10;
    this.ctx.beginPath();
    this.ctx.moveTo(10, trayY);
    this.ctx.lineTo(this.canvas.width - 10, trayY);
    this.ctx.strokeStyle = 'rgba(59, 36, 18, 0.4)';
    this.ctx.lineWidth = 2;
    this.ctx.setLineDash([5, 5]);
    this.ctx.stroke();
    this.ctx.setLineDash([]);

    // Draw pieces
    const drawPiece = (p) => {
      this.ctx.drawImage(
        p.canvas, 
        p.x - this.w/2 - p.padding, 
        p.y - this.h/2 - p.padding
      );
    };

    this.pieces.forEach(p => {
      if (p !== this.draggedPiece) drawPiece(p);
    });
    if (this.draggedPiece) {
      this.ctx.shadowColor = 'rgba(0,0,0,0.4)';
      this.ctx.shadowBlur = 10;
      this.ctx.shadowOffsetX = 5;
      this.ctx.shadowOffsetY = 5;
      drawPiece(this.draggedPiece);
      this.ctx.shadowColor = 'transparent';
    }
  }

  bindEvents() {
    const getPos = (e) => {
      const rect = this.canvas.getBoundingClientRect();
      const clientX = e.touches ? e.touches[0].clientX : e.clientX;
      const clientY = e.touches ? e.touches[0].clientY : e.clientY;
      const scaleX = rect.width ? (this.canvas.width / rect.width) : 1;
      const scaleY = rect.height ? (this.canvas.height / rect.height) : 1;
      return {
        x: (clientX - rect.left) * scaleX,
        y: (clientY - rect.top) * scaleY
      };
    };

    const handleDown = (e) => {
      if (e.touches && e.touches.length > 1) return;
      const { x, y } = getPos(e);
      
      for (let i = this.pieces.length - 1; i >= 0; i--) {
        const p = this.pieces[i];
        if (Math.abs(p.x - x) < this.w/2 && Math.abs(p.y - y) < this.h/2) {
          this.isDragging = true;
          this.draggedPiece = p;
          
          const yOffset = e.touches ? -40 : 0;
          this.dragOffsetX = p.x - x;
          this.dragOffsetY = p.y - y + yOffset;
          
          if (p.currentSlot) {
            p.currentSlot.piece = null;
            p.currentSlot = null;
          }
          
          this.pieces.splice(i, 1);
          this.pieces.push(p);
          
          if (typeof Sound !== 'undefined' && Sound.playFlip) Sound.playFlip();
          this.render();
          e.preventDefault();
          break;
        }
      }
    };

    const handleMove = (e) => {
      if (!this.isDragging || !this.draggedPiece) return;
      const { x, y } = getPos(e);
      this.draggedPiece.x = x + this.dragOffsetX;
      this.draggedPiece.y = y + this.dragOffsetY;
      this.render();
      e.preventDefault();
    };

    const handleUp = (e) => {
      if (!this.isDragging || !this.draggedPiece) return;
      const p = this.draggedPiece;
      this.isDragging = false;
      this.draggedPiece = null;

      let nearestSlot = null;
      let minDist = (this.w + this.h) / 2;

      this.slots.forEach(s => {
        if (s.piece) return;
        const dist = Math.hypot(s.x - p.x, s.y - p.y);
        if (dist < minDist) {
          minDist = dist;
          nearestSlot = s;
        }
      });

      if (nearestSlot) {
        p.x = nearestSlot.x;
        p.y = nearestSlot.y;
        p.currentSlot = nearestSlot;
        nearestSlot.piece = p;
        if (typeof Sound !== 'undefined' && Sound.playMatch) Sound.playMatch();
      } else {
        if (typeof Sound !== 'undefined' && Sound.playMismatch) Sound.playMismatch();
      }

      this.render();
      this.checkWin();
    };

    this.canvas.addEventListener('mousedown', handleDown, { passive: false });
    this.canvas.addEventListener('mousemove', handleMove, { passive: false });
    window.addEventListener('mouseup', handleUp);
    
    this.canvas.addEventListener('touchstart', handleDown, { passive: false });
    this.canvas.addEventListener('touchmove', handleMove, { passive: false });
    window.addEventListener('touchend', handleUp);
  }

  checkWin() {
    let allCorrect = true;
    for (let p of this.pieces) {
      if (!p.currentSlot || p.currentSlot.r !== p.targetR || p.currentSlot.c !== p.targetC) {
        allCorrect = false;
        break;
      }
    }
    
    if (allCorrect) {
      if (typeof Sound !== 'undefined' && Sound.playVictory) Sound.playVictory();
      if (this.onComplete) {
        this.onComplete();
      }
    }
  }
}
