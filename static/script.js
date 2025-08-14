const PIECES = {
  'K': '♔', 'Q': '♕', 'R': '♖', 'B': '♗', 'N': '♘', 'P': '♙',
  'k': '♚', 'q': '♛', 'r': '♜', 'b': '♝', 'n': '♞', 'p': '♟'
};

const INITIAL_BOARD = [
  ['r', 'n', 'b', 'q', 'k', 'b', 'n', 'r'],
  ['p', 'p', 'p', 'p', 'p', 'p', 'p', 'p'],
  [null, null, null, null, null, null, null, null],
  [null, null, null, null, null, null, null, null],
  [null, null, null, null, null, null, null, null],
  [null, null, null, null, null, null, null, null],
  ['P', 'P', 'P', 'P', 'P', 'P', 'P', 'P'],
  ['R', 'N', 'B', 'Q', 'K', 'B', 'N', 'R']
];

class ChessGame {
  constructor() {
    this.board = this.copyBoard(INITIAL_BOARD);
    this.currentTurn = 'white';
    this.playerColor = null;
    this.selectedSquare = null;
    this.possibleMoves = [];
    this.moveHistory = [];
    this.capturedPieces = { white: [], black: [] };
    this.lastMove = null;
    this.gameOver = false;
    this.boardFlipped = false;

    this.initializeElements();
    this.setupEventListeners();
    this.showColorModal();
  }

  initializeElements() {
    this.boardElement = document.getElementById('chess-board');
    this.statusElement = document.getElementById('status');
    this.turnIndicator = document.getElementById('turn-indicator');
    this.moveListElement = document.getElementById('move-list');
    this.whiteCapturedElement = document.getElementById('white-captured');
    this.blackCapturedElement = document.getElementById('black-captured');

    this.colorModal = document.getElementById('color-modal');
    this.promotionModal = document.getElementById('promotion-modal');
    this.gameOverModal = document.getElementById('game-over-modal');
  }

  setupEventListeners() {
    document.getElementById('choose-white').addEventListener('click', () => {
      this.startGame('white');
    });

    document.getElementById('choose-black').addEventListener('click', () => {
      this.startGame('black');
    });

    document.getElementById('new-game').addEventListener('click', () => {
      this.resetGame();
    });

    document.getElementById('flip-board').addEventListener('click', () => {
      this.flipBoard();
    });

    document.getElementById('undo-move').addEventListener('click', () => {
      this.undoMove();
    });

    document.getElementById('play-again').addEventListener('click', () => {
      this.resetGame();
    });

    document.querySelectorAll('.promotion-btn').forEach(btn => {
      btn.addEventListener('click', (e) => {
        const piece = e.target.dataset.piece;
        this.completePromotion(piece);
      });
    });
  }

  showColorModal() {
    this.colorModal.classList.add('active');
  }

  hideColorModal() {
    this.colorModal.classList.remove('active');
  }

  startGame(color) {
    this.playerColor = color;
    this.hideColorModal();
    this.renderBoard();
    this.updateStatus('Game started! You are playing as ' + color);
    this.updateTurnIndicator();

    if (color === 'black') {
      this.makeAIMove();
    }
  }

  copyBoard(board) {
    return board.map(row => [...row]);
  }

  renderBoard() {
    this.boardElement.innerHTML = '';

    for (let row = 0; row < 8; row++) {
      for (let col = 0; col < 8; col++) {
        const displayRow = this.boardFlipped ? 7 - row : row;
        const displayCol = this.boardFlipped ? 7 - col : col;

        const square = document.createElement('div');
        square.className = 'square';
        square.className += (row + col) % 2 === 0 ? ' light' : ' dark';
        square.dataset.row = displayRow;
        square.dataset.col = displayCol;

        const piece = this.board[displayRow][displayCol];
        if (piece) {
          square.textContent = PIECES[piece];
        }

        if (this.selectedSquare &&
          this.selectedSquare.row === displayRow &&
          this.selectedSquare.col === displayCol) {
          square.classList.add('selected');
        }

        if (this.possibleMoves.some(m => m.row === displayRow && m.col === displayCol)) {
          if (this.board[displayRow][displayCol]) {
            square.classList.add('possible-capture');
          } else {
            square.classList.add('possible-move');
          }
        }

        if (this.lastMove) {
          if ((this.lastMove.from.row === displayRow && this.lastMove.from.col === displayCol) ||
            (this.lastMove.to.row === displayRow && this.lastMove.to.col === displayCol)) {
            square.classList.add('last-move');
          }
        }

        square.addEventListener('click', () => this.handleSquareClick(displayRow, displayCol));

        this.boardElement.appendChild(square);
      }
    }
  }

  handleSquareClick(row, col) {
    if (this.gameOver || this.currentTurn !== this.playerColor) return;

    const piece = this.board[row][col];

    if (this.selectedSquare) {
      if (this.possibleMoves.some(m => m.row === row && m.col === col)) {
        this.makeMove(this.selectedSquare.row, this.selectedSquare.col, row, col);
      } else if (piece && this.isPieceOwnedByCurrentPlayer(piece)) {
        this.selectSquare(row, col);
      } else {
        this.selectedSquare = null;
        this.possibleMoves = [];
        this.renderBoard();
      }
    } else {
      // Select a piece
      if (piece && this.isPieceOwnedByCurrentPlayer(piece)) {
        this.selectSquare(row, col);
      }
    }
  }

  selectSquare(row, col) {
    this.selectedSquare = { row, col };
    this.possibleMoves = this.getValidMoves(row, col);
    this.renderBoard();
  }

  isPieceOwnedByCurrentPlayer(piece) {
    if (this.currentTurn === 'white') {
      return piece === piece.toUpperCase();
    } else {
      return piece === piece.toLowerCase();
    }
  }

  getValidMoves(row, col) {
    const piece = this.board[row][col];
    if (!piece) return [];

    const moves = [];
    const pieceType = piece.toLowerCase();
    const isWhite = piece === piece.toUpperCase();

    switch (pieceType) {
      case 'p':
        moves.push(...this.getPawnMoves(row, col, isWhite));
        break;
      case 'n':
        moves.push(...this.getKnightMoves(row, col, isWhite));
        break;
      case 'b':
        moves.push(...this.getBishopMoves(row, col, isWhite));
        break;
      case 'r':
        moves.push(...this.getRookMoves(row, col, isWhite));
        break;
      case 'q':
        moves.push(...this.getQueenMoves(row, col, isWhite));
        break;
      case 'k':
        moves.push(...this.getKingMoves(row, col, isWhite));
        break;
    }

    return moves.filter(move => !this.wouldBeInCheck(row, col, move.row, move.col, isWhite));
  }

  getPawnMoves(row, col, isWhite) {
    const moves = [];
    const direction = isWhite ? -1 : 1;
    const startRow = isWhite ? 6 : 1;

    if (this.isValidSquare(row + direction, col) && !this.board[row + direction][col]) {
      moves.push({ row: row + direction, col });

      if (row === startRow && !this.board[row + 2 * direction][col]) {
        moves.push({ row: row + 2 * direction, col });
      }
    }

    for (const dc of [-1, 1]) {
      const newRow = row + direction;
      const newCol = col + dc;
      if (this.isValidSquare(newRow, newCol)) {
        const target = this.board[newRow][newCol];
        if (target && this.isOpponentPiece(target, isWhite)) {
          moves.push({ row: newRow, col: newCol });
        }
      }
    }

    return moves;
  }

  getKnightMoves(row, col, isWhite) {
    const moves = [];
    const knightMoves = [
      [-2, -1], [-2, 1], [-1, -2], [-1, 2],
      [1, -2], [1, 2], [2, -1], [2, 1]
    ];

    for (const [dr, dc] of knightMoves) {
      const newRow = row + dr;
      const newCol = col + dc;
      if (this.isValidSquare(newRow, newCol)) {
        const target = this.board[newRow][newCol];
        if (!target || this.isOpponentPiece(target, isWhite)) {
          moves.push({ row: newRow, col: newCol });
        }
      }
    }

    return moves;
  }

  getBishopMoves(row, col, isWhite) {
    const moves = [];
    const directions = [[-1, -1], [-1, 1], [1, -1], [1, 1]];

    for (const [dr, dc] of directions) {
      for (let i = 1; i < 8; i++) {
        const newRow = row + dr * i;
        const newCol = col + dc * i;
        if (!this.isValidSquare(newRow, newCol)) break;

        const target = this.board[newRow][newCol];
        if (!target) {
          moves.push({ row: newRow, col: newCol });
        } else {
          if (this.isOpponentPiece(target, isWhite)) {
            moves.push({ row: newRow, col: newCol });
          }
          break;
        }
      }
    }

    return moves;
  }

  getRookMoves(row, col, isWhite) {
    const moves = [];
    const directions = [[-1, 0], [1, 0], [0, -1], [0, 1]];

    for (const [dr, dc] of directions) {
      for (let i = 1; i < 8; i++) {
        const newRow = row + dr * i;
        const newCol = col + dc * i;
        if (!this.isValidSquare(newRow, newCol)) break;

        const target = this.board[newRow][newCol];
        if (!target) {
          moves.push({ row: newRow, col: newCol });
        } else {
          if (this.isOpponentPiece(target, isWhite)) {
            moves.push({ row: newRow, col: newCol });
          }
          break;
        }
      }
    }

    return moves;
  }

  getQueenMoves(row, col, isWhite) {
    return [
      ...this.getBishopMoves(row, col, isWhite),
      ...this.getRookMoves(row, col, isWhite)
    ];
  }

  getKingMoves(row, col, isWhite) {
    const moves = [];
    const directions = [
      [-1, -1], [-1, 0], [-1, 1],
      [0, -1], [0, 1],
      [1, -1], [1, 0], [1, 1]
    ];

    for (const [dr, dc] of directions) {
      const newRow = row + dr;
      const newCol = col + dc;
      if (this.isValidSquare(newRow, newCol)) {
        const target = this.board[newRow][newCol];
        if (!target || this.isOpponentPiece(target, isWhite)) {
          moves.push({ row: newRow, col: newCol });
        }
      }
    }

    return moves;
  }

  isValidSquare(row, col) {
    return row >= 0 && row < 8 && col >= 0 && col < 8;
  }

  isOpponentPiece(piece, isWhite) {
    return isWhite ? piece === piece.toLowerCase() : piece === piece.toUpperCase();
  }

  wouldBeInCheck(fromRow, fromCol, toRow, toCol, isWhite) {
    const tempBoard = this.copyBoard(this.board);
    const capturedPiece = tempBoard[toRow][toCol];
    tempBoard[toRow][toCol] = tempBoard[fromRow][fromCol];
    tempBoard[fromRow][fromCol] = null;

    let kingRow = -1, kingCol = -1;
    for (let r = 0; r < 8; r++) {
      for (let c = 0; c < 8; c++) {
        const piece = tempBoard[r][c];
        if (piece && piece.toLowerCase() === 'k' &&
          (isWhite ? piece === 'K' : piece === 'k')) {
          kingRow = r;
          kingCol = c;
          break;
        }
      }
      if (kingRow !== -1) break;
    }

    return this.isSquareUnderAttack(tempBoard, kingRow, kingCol, !isWhite);
  }

  isSquareUnderAttack(board, row, col, byWhite) {
    for (let r = 0; r < 8; r++) {
      for (let c = 0; c < 8; c++) {
        const piece = board[r][c];
        if (!piece) continue;

        const isPieceWhite = piece === piece.toUpperCase();
        if (isPieceWhite !== byWhite) continue;

        if (this.canPieceAttack(board, r, c, row, col, piece)) {
          return true;
        }
      }
    }
    return false;
  }

  canPieceAttack(board, fromRow, fromCol, toRow, toCol, piece) {
    const pieceType = piece.toLowerCase();
    const dr = toRow - fromRow;
    const dc = toCol - fromCol;
    const isWhite = piece === piece.toUpperCase();

    switch (pieceType) {
      case 'p':
        const direction = isWhite ? -1 : 1;
        return dr === direction && Math.abs(dc) === 1;

      case 'n':
        return (Math.abs(dr) === 2 && Math.abs(dc) === 1) ||
          (Math.abs(dr) === 1 && Math.abs(dc) === 2);

      case 'b':
        if (Math.abs(dr) !== Math.abs(dc)) return false;
        return this.isPathClear(board, fromRow, fromCol, toRow, toCol);

      case 'r':
        if (dr !== 0 && dc !== 0) return false;
        return this.isPathClear(board, fromRow, fromCol, toRow, toCol);

      case 'q':
        if (dr !== 0 && dc !== 0 && Math.abs(dr) !== Math.abs(dc)) return false;
        return this.isPathClear(board, fromRow, fromCol, toRow, toCol);

      case 'k':
        return Math.abs(dr) <= 1 && Math.abs(dc) <= 1;
    }
    return false;
  }

  isPathClear(board, fromRow, fromCol, toRow, toCol) {
    const dr = Math.sign(toRow - fromRow);
    const dc = Math.sign(toCol - fromCol);
    let r = fromRow + dr;
    let c = fromCol + dc;

    while (r !== toRow || c !== toCol) {
      if (board[r][c]) return false;
      r += dr;
      c += dc;
    }
    return true;
  }

  makeMove(fromRow, fromCol, toRow, toCol, isPlayerMove = true) {
    const piece = this.board[fromRow][fromCol];
    const capturedPiece = this.board[toRow][toCol];

    const isPawn = piece.toLowerCase() === 'p';
    const isPromoting = isPawn && ((piece === 'P' && toRow === 0) || (piece === 'p' && toRow === 7));

    if (isPromoting && isPlayerMove) {
      this.pendingPromotion = { fromRow, fromCol, toRow, toCol, piece, capturedPiece };
      this.showPromotionModal();
      return;
    }

    const moveNotation = this.getMoveNotation(fromRow, fromCol, toRow, toCol, piece, capturedPiece);

    this.board[toRow][toCol] = piece;
    this.board[fromRow][fromCol] = null;

    if (capturedPiece) {
      const capturedColor = capturedPiece === capturedPiece.toUpperCase() ? 'white' : 'black';
      this.capturedPieces[capturedColor].push(capturedPiece);
      this.updateCapturedPieces();
    }

    this.moveHistory.push({
      from: { row: fromRow, col: fromCol },
      to: { row: toRow, col: toCol },
      piece: piece,
      captured: capturedPiece,
      notation: moveNotation
    });
    this.lastMove = this.moveHistory[this.moveHistory.length - 1];
    this.updateMoveList();

    this.selectedSquare = null;
    this.possibleMoves = [];

    this.currentTurn = this.currentTurn === 'white' ? 'black' : 'white';
    this.updateTurnIndicator();

    if (this.checkGameOver()) {
      return;
    }

    this.renderBoard();

    if (isPlayerMove && this.currentTurn !== this.playerColor) {
      setTimeout(() => this.makeAIMove(), 500);
    }
  }

  showPromotionModal() {
    const isWhite = this.currentTurn === 'white';
    const pieces = isWhite ? ['♕', '♖', '♗', '♘'] : ['♛', '♜', '♝', '♞'];
    const buttons = document.querySelectorAll('.promotion-btn');
    buttons.forEach((btn, i) => {
      btn.textContent = pieces[i];
    });

    this.promotionModal.classList.add('active');
  }

  completePromotion(pieceType) {
    this.promotionModal.classList.remove('active');

    const p = this.pendingPromotion;
    const isWhite = p.piece === p.piece.toUpperCase();
    const newPiece = isWhite ? pieceType.toUpperCase() : pieceType.toLowerCase();

    this.board[p.toRow][p.toCol] = newPiece;
    this.board[p.fromRow][p.fromCol] = null;

    if (p.capturedPiece) {
      const capturedColor = p.capturedPiece === p.capturedPiece.toUpperCase() ? 'white' : 'black';
      this.capturedPieces[capturedColor].push(p.capturedPiece);
      this.updateCapturedPieces();
    }

    const moveNotation = this.getMoveNotation(p.fromRow, p.fromCol, p.toRow, p.toCol, p.piece, p.capturedPiece) + '=' + pieceType.toUpperCase();
    this.moveHistory.push({
      from: { row: p.fromRow, col: p.fromCol },
      to: { row: p.toRow, col: p.toCol },
      piece: newPiece,
      captured: p.capturedPiece,
      notation: moveNotation
    });
    this.lastMove = this.moveHistory[this.moveHistory.length - 1];
    this.updateMoveList();

    this.pendingPromotion = null;

    this.currentTurn = this.currentTurn === 'white' ? 'black' : 'white';
    this.updateTurnIndicator();

    if (this.checkGameOver()) {
      return;
    }

    this.renderBoard();

    if (this.currentTurn !== this.playerColor) {
      setTimeout(() => this.makeAIMove(), 500);
    }
  }

  getMoveNotation(fromRow, fromCol, toRow, toCol, piece, captured) {
    const files = 'abcdefgh';
    const fromFile = files[fromCol];
    const toFile = files[toCol];
    const fromRank = 8 - fromRow;
    const toRank = 8 - toRow;

    let notation = '';
    const pieceType = piece.toUpperCase();

    if (pieceType !== 'P') {
      notation += pieceType;
    }

    if (captured) {
      if (pieceType === 'P') {
        notation += fromFile;
      }
      notation += 'x';
    }

    notation += toFile + toRank;

    return notation;
  }

  checkGameOver() {
    const isWhiteTurn = this.currentTurn === 'white';
    const inCheck = this.isInCheck(isWhiteTurn);
    const hasLegalMoves = this.hasLegalMoves(isWhiteTurn);

    if (!hasLegalMoves) {
      this.gameOver = true;
      if (inCheck) {
        const winner = isWhiteTurn ? 'Black' : 'White';
        this.showGameOver(`${winner} wins by checkmate!`);
      } else {
        this.showGameOver('Game drawn by stalemate!');
      }
      return true;
    }

    if (this.isInsufficientMaterial()) {
      this.gameOver = true;
      this.showGameOver('Game drawn by insufficient material!');
      return true;
    }

    return false;
  }

  isInCheck(isWhite) {
    // Find king
    let kingRow = -1, kingCol = -1;
    for (let r = 0; r < 8; r++) {
      for (let c = 0; c < 8; c++) {
        const piece = this.board[r][c];
        if (piece && piece.toLowerCase() === 'k' &&
          (isWhite ? piece === 'K' : piece === 'k')) {
          kingRow = r;
          kingCol = c;
          break;
        }
      }
      if (kingRow !== -1) break;
    }

    return this.isSquareUnderAttack(this.board, kingRow, kingCol, !isWhite);
  }

  hasLegalMoves(isWhite) {
    for (let r = 0; r < 8; r++) {
      for (let c = 0; c < 8; c++) {
        const piece = this.board[r][c];
        if (!piece) continue;

        const isPieceWhite = piece === piece.toUpperCase();
        if (isPieceWhite !== isWhite) continue;

        const moves = this.getValidMoves(r, c);
        if (moves.length > 0) return true;
      }
    }
    return false;
  }

  isInsufficientMaterial() {
    const pieces = { white: [], black: [] };

    for (let r = 0; r < 8; r++) {
      for (let c = 0; c < 8; c++) {
        const piece = this.board[r][c];
        if (piece) {
          const color = piece === piece.toUpperCase() ? 'white' : 'black';
          pieces[color].push(piece.toLowerCase());
        }
      }
    }

    // King vs King
    if (pieces.white.length === 1 && pieces.black.length === 1) return true;

    // King and Bishop/Knight vs King
    if ((pieces.white.length === 2 && pieces.black.length === 1) ||
      (pieces.white.length === 1 && pieces.black.length === 2)) {
      const morePieces = pieces.white.length === 2 ? pieces.white : pieces.black;
      if (morePieces.includes('b') || morePieces.includes('n')) return true;
    }

    return false;
  }

  showGameOver(message) {
    document.getElementById('game-message').textContent = message;
    this.gameOverModal.classList.add('active');
    this.updateStatus(message);
  }

  async makeAIMove() {
    this.updateStatus('AI is thinking...');

    const difficulty = document.getElementById('ai-difficulty').value;
    const moveTime = parseInt(document.getElementById('move-time').value);

    const depthMap = {
      easy: 4,
      medium: 6,
      hard: 8,
      expert: 10
    };

    try {
      const response = await fetch('http://localhost:8000/api/get-move', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          board: this.boardToFEN(),
          depth: depthMap[difficulty],
          moveTime: moveTime
        })
      });

      if (!response.ok) throw new Error('AI request failed');

      const data = await response.json();
      const move = this.parseMoveFromUCI(data.move);

      if (move) {
        this.makeMove(move.from.row, move.from.col, move.to.row, move.to.col, false);
      }
    } catch (error) {
      console.error('AI move failed:', error);
      this.makeRandomMove();
    }
  }

  makeRandomMove() {
    // Fallback for when AI is not available
    const isWhite = this.currentTurn === 'white';
    const legalMoves = [];

    for (let r = 0; r < 8; r++) {
      for (let c = 0; c < 8; c++) {
        const piece = this.board[r][c];
        if (!piece) continue;

        const isPieceWhite = piece === piece.toUpperCase();
        if (isPieceWhite !== isWhite) continue;

        const moves = this.getValidMoves(r, c);
        for (const move of moves) {
          legalMoves.push({ from: { row: r, col: c }, to: move });
        }
      }
    }

    if (legalMoves.length > 0) {
      const randomMove = legalMoves[Math.floor(Math.random() * legalMoves.length)];
      this.makeMove(randomMove.from.row, randomMove.from.col,
        randomMove.to.row, randomMove.to.col, false);
    }
  }

  boardToFEN() {
    let fen = '';

    for (let row = 0; row < 8; row++) {
      let emptyCount = 0;

      for (let col = 0; col < 8; col++) {
        const piece = this.board[row][col];

        if (piece) {
          if (emptyCount > 0) {
            fen += emptyCount;
            emptyCount = 0;
          }
          fen += piece;
        } else {
          emptyCount++;
        }
      }

      if (emptyCount > 0) {
        fen += emptyCount;
      }

      if (row < 7) {
        fen += '/';
      }
    }

    fen += ' ' + (this.currentTurn === 'white' ? 'w' : 'b');
    fen += ' KQkq - 0 1'; // Simplified - assumes all castling rights

    return fen;
  }

  parseMoveFromUCI(uci) {
    if (!uci || uci.length < 4) return null;

    const files = 'abcdefgh';
    const fromCol = files.indexOf(uci[0]);
    const fromRow = 8 - parseInt(uci[1]);
    const toCol = files.indexOf(uci[2]);
    const toRow = 8 - parseInt(uci[3]);

    return {
      from: { row: fromRow, col: fromCol },
      to: { row: toRow, col: toCol }
    };
  }

  updateStatus(message) {
    this.statusElement.textContent = message;
  }

  updateTurnIndicator() {
    const turn = this.currentTurn.charAt(0).toUpperCase() + this.currentTurn.slice(1);
    this.turnIndicator.textContent = `${turn}'s turn`;
    this.turnIndicator.style.background = this.currentTurn === 'white' ? '#e8f5e9' : '#333';
    this.turnIndicator.style.color = this.currentTurn === 'white' ? '#2e7d32' : 'white';
  }

  updateMoveList() {
    const moves = this.moveHistory;
    let html = '';

    for (let i = 0; i < moves.length; i += 2) {
      const moveNum = Math.floor(i / 2) + 1;
      html += '<div class="move-entry">';
      html += `<span class="move-number">${moveNum}.</span>`;
      html += `<span class="white-move">${moves[i].notation}</span>`;
      if (moves[i + 1]) {
        html += `<span class="black-move">${moves[i + 1].notation}</span>`;
      }
      html += '</div>';
    }

    this.moveListElement.innerHTML = html;
    this.moveListElement.scrollTop = this.moveListElement.scrollHeight;
  }

  updateCapturedPieces() {
    this.whiteCapturedElement.innerHTML = this.capturedPieces.white
      .map(p => `<span class="captured-piece">${PIECES[p]}</span>`).join('');
    this.blackCapturedElement.innerHTML = this.capturedPieces.black
      .map(p => `<span class="captured-piece">${PIECES[p]}</span>`).join('');
  }

  flipBoard() {
    this.boardFlipped = !this.boardFlipped;
    this.renderBoard();
  }

  resetGame() {
    this.board = this.copyBoard(INITIAL_BOARD);
    this.currentTurn = 'white';
    this.selectedSquare = null;
    this.possibleMoves = [];
    this.moveHistory = [];
    this.capturedPieces = { white: [], black: [] };
    this.lastMove = null;
    this.gameOver = false;

    this.gameOverModal.classList.remove('active');
    this.updateMoveList();
    this.updateCapturedPieces();
    this.showColorModal();
  }
}

document.addEventListener('DOMContentLoaded', () => {
  new ChessGame();
});