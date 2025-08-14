
import chess
import chess.polyglot
import math
import random
import time
from dataclasses import dataclass

MATE_SCORE = 10_000_000
INFTY = 10_000_000
DRAW_SCORE = 0

def is_mate_score(score: int) -> bool:
    return abs(score) >= MATE_SCORE - 1000

def sign(x):
    return (x > 0) - (x < 0)

def phase_score(board: chess.Board) -> int:
    """Game phase (0 = endgame, 24 = opening-ish)."""
    phase = 0
    phase += 1 * (len(board.pieces(chess.KNIGHT, chess.WHITE)) + len(board.pieces(chess.KNIGHT, chess.BLACK)))
    phase += 1 * (len(board.pieces(chess.BISHOP, chess.WHITE)) + len(board.pieces(chess.BISHOP, chess.BLACK)))
    phase += 2 * (len(board.pieces(chess.ROOK, chess.WHITE)) + len(board.pieces(chess.ROOK, chess.BLACK)))
    phase += 4 * (len(board.pieces(chess.QUEEN, chess.WHITE)) + len(board.pieces(chess.QUEEN, chess.BLACK)))
    return min(24, int(phase * 24 / 16))

def mirror_index(sq: int) -> int:
    return chess.square_mirror(sq)

PIECE_VALUES_MG = {
    chess.PAWN:   100,
    chess.KNIGHT: 320,
    chess.BISHOP: 330,
    chess.ROOK:   500,
    chess.QUEEN:  900,
    chess.KING:     0,
}

PIECE_VALUES_EG = {
    chess.PAWN:   120,
    chess.KNIGHT: 300,
    chess.BISHOP: 330,
    chess.ROOK:   520,
    chess.QUEEN:  900,
    chess.KING:     0,
}

PAWN_PST = [
     0,   0,   0,   0,   0,   0,   0,   0,
    50,  50,  50,  50,  50,  50,  50,  50,
    10,  10,  20,  30,  30,  20,  10,  10,
     5,   5,  10,  25,  25,  10,   5,   5,
     0,   0,   0,  20,  20,   0,   0,   0,
     5,  -5, -10,   0,   0,-10,  -5,   5,
     5,  10,  10, -20, -20,  10,  10,   5,
     0,   0,   0,   0,   0,   0,   0,   0
]

KNIGHT_PST = [
    -50,-40,-30,-30,-30,-30,-40,-50,
    -40,-20,  0,  0,  0,  0,-20,-40,
    -30,  0, 10, 15, 15, 10,  0,-30,
    -30,  5, 15, 20, 20, 15,  5,-30,
    -30,  0, 15, 20, 20, 15,  0,-30,
    -30,  5, 10, 15, 15, 10,  5,-30,
    -40,-20,  0,  5,  5,  0,-20,-40,
    -50,-40,-30,-30,-30,-30,-40,-50
]

BISHOP_PST = [
    -20,-10,-10,-10,-10,-10,-10,-20,
    -10,  0,  0,  0,  0,  0,  0,-10,
    -10,  0,  5, 10, 10,  5,  0,-10,
    -10,  5,  5, 10, 10,  5,  5,-10,
    -10,  0, 10, 10, 10, 10,  0,-10,
    -10, 10, 10, 10, 10, 10, 10,-10,
    -10,  5,  0,  0,  0,  0,  5,-10,
    -20,-10,-10,-10,-10,-10,-10,-20
]

ROOK_PST = [
     0,  0,  0,  0,  0,  0,  0,  0,
     5, 10, 10, 10, 10, 10, 10,  5,
    -5,  0,  0,  0,  0,  0,  0, -5,
    -5,  0,  0,  0,  0,  0,  0, -5,
    -5,  0,  0,  0,  0,  0,  0, -5,
    -5,  0,  0,  0,  0,  0,  0, -5,
    -5,  0,  0,  0,  0,  0,  0, -5,
     0,  0,  0,  5,  5,  0,  0,  0
]

KING_PST_MG = [
    -30,-40,-40,-50,-50,-40,-40,-30,
    -30,-40,-40,-50,-50,-40,-40,-30,
    -30,-40,-40,-50,-50,-40,-40,-30,
    -30,-40,-40,-50,-50,-40,-40,-30,
    -20,-30,-30,-40,-40,-30,-30,-20,
    -10,-20,-20,-20,-20,-20,-20,-10,
     20, 20,  0,  0,  0,  0, 20, 20,
     20, 30, 10,  0,  0, 10, 30, 20
]

KING_PST_EG = [
    -50,-40,-30,-20,-20,-30,-40,-50,
    -30,-20,-10,  0,  0,-10,-20,-30,
    -30,-10, 20, 30, 30, 20,-10,-30,
    -30,-10, 30, 40, 40, 30,-10,-30,
    -30,-10, 30, 40, 40, 30,-10,-30,
    -30,-10, 20, 30, 30, 20,-10,-30,
    -30,-30,  0,  0,  0,  0,-30,-30,
    -50,-30,-30,-30,-30,-30,-30,-50
]

PST_MAP = {
    chess.PAWN: (PAWN_PST, PAWN_PST),
    chess.KNIGHT: (KNIGHT_PST, KNIGHT_PST),
    chess.BISHOP: (BISHOP_PST, BISHOP_PST),
    chess.ROOK: (ROOK_PST, ROOK_PST),
    chess.QUEEN: (None, None),
    chess.KING: (KING_PST_MG, KING_PST_EG),
}

@dataclass
class TTEntry:
    depth: int
    score: int
    flag: int   # 0=exact, -1=alpha, 1=beta
    move: chess.Move | None

class StrongChessAI:
    def __init__(self, book_path: str | None = None):
        self.book = None
        if book_path:
            try:
                self.book = chess.polyglot.open_reader(book_path)
            except Exception:
                self.book = None

        self.tt: dict[int, TTEntry] = {}
        self.killer_moves: dict[int, list[chess.Move]] = {}  # depth -> [killer1, killer2]
        self.history_heuristic: dict[tuple[int, int], int] = {}  # (from,to) -> score

        # time controls
        self.hard_time_limit = 3.0   # absolute max per move (seconds)
        self.soft_time_limit = 2.0   # typical thinking time per move (seconds)

    # --------- Keys ---------

    def tt_key(self, board: chess.Board) -> int:
        # Try to use a stable, fast hash if available
        try:
            return board.transposition_key()
        except Exception:
            try:
                return board._transposition_key()
            except Exception:
                return hash(board.board_fen()) ^ hash(board.castling_rights) ^ hash(board.ep_square)

    # --------- Evaluation ---------

    def evaluate(self, board: chess.Board) -> int:
        # Check game end
        if board.is_checkmate():
            return -MATE_SCORE + 1 if board.turn else MATE_SCORE - 1
        if board.is_stalemate() or board.is_insufficient_material() or board.can_claim_fifty_moves():
            return DRAW_SCORE

        mg = 0
        eg = 0

        # Material + PSTs
        for color in [chess.WHITE, chess.BLACK]:
            signc = 1 if color == chess.WHITE else -1

            for piece_type, (pst_mg, pst_eg) in PST_MAP.items():
                squares = board.pieces(piece_type, color)
                pv_mg = PIECE_VALUES_MG[piece_type] if piece_type in PIECE_VALUES_MG else 0
                pv_eg = PIECE_VALUES_EG[piece_type] if piece_type in PIECE_VALUES_EG else 0

                for sq in squares:
                    mg += signc * pv_mg
                    eg += signc * pv_eg
                    if pst_mg is not None:
                        mg += signc * pst_mg[sq if color == chess.WHITE else mirror_index(sq)]
                    if pst_eg is not None:
                        eg += signc * pst_eg[sq if color == chess.WHITE else mirror_index(sq)]

        # Bishop pair
        if len(board.pieces(chess.BISHOP, chess.WHITE)) >= 2:
            mg += 30; eg += 40
        if len(board.pieces(chess.BISHOP, chess.BLACK)) >= 2:
            mg -= 30; eg -= 40

        # Rooks on (semi-)open files
        mg += self._rooks_file_bonus(board, chess.WHITE)
        mg -= self._rooks_file_bonus(board, chess.BLACK)

        # Pawn structure: doubled/isolated (lightweight)
        mg += self._pawn_structure(board, chess.WHITE)
        mg -= self._pawn_structure(board, chess.BLACK)

        # Mobility (very light)
        turn_save = board.turn
        board.turn = chess.WHITE
        wm = board.legal_moves.count()
        board.turn = chess.BLACK
        bm = board.legal_moves.count()
        board.turn = turn_save
        mg += (wm - bm)

        # Tapered eval
        phase = phase_score(board)
        score = (mg * phase + eg * (24 - phase)) // 24

        # Tempo
        score += 10 if board.turn == chess.WHITE else -10

        return score

    def _rooks_file_bonus(self, board: chess.Board, color: bool) -> int:
        bonus = 0
        pawns = board.pieces(chess.PAWN, not color)
        mypawns = board.pieces(chess.PAWN, color)
        for sq in board.pieces(chess.ROOK, color):
            file_idx = chess.square_file(sq)
            file_mask = {s for s in range(file_idx, 64, 8)}
            has_enemy_pawn = any((s in pawns) for s in file_mask)
            has_my_pawn = any((s in mypawns) for s in file_mask)
            if not has_my_pawn and not has_enemy_pawn:
                bonus += 15  # open file
            elif not has_my_pawn and has_enemy_pawn:
                bonus += 8  # semi-open
        return bonus

    def _pawn_structure(self, board: chess.Board, color: bool) -> int:
        pawns = list(board.pieces(chess.PAWN, color))
        if not pawns: return 0
        files = [chess.square_file(p) for p in pawns]
        score = 0
        # doubled
        for f in range(8):
            cnt = files.count(f)
            if cnt > 1:
                score -= 15 * (cnt - 1)
        # isolated
        file_set = set(files)
        for f in files:
            if (f-1) not in file_set and (f+1) not in file_set:
                score -= 12
        return score

    # --------- Move ordering ---------

    MVV_LVA_SCORES = None

    def mvv_lva(self, board: chess.Board, move: chess.Move) -> int:
        if self.MVV_LVA_SCORES is None:
            order = [None, 100, 300, 325, 500, 900, 20000]
            self.MVV_LVA_SCORES = [[0]*7 for _ in range(7)]
            for v in range(1,7):
                for a in range(1,7):
                    self.MVV_LVA_SCORES[v][a] = order[v] * 10 - order[a]
        victim = board.piece_at(move.to_square)
        attacker = board.piece_at(move.from_square)
        if victim and attacker:
            return self.MVV_LVA_SCORES[victim.piece_type][attacker.piece_type]
        return 0

    def order_moves(self, board: chess.Board, moves, tt_move: chess.Move | None, depth: int):
        killers = self.killer_moves.get(depth, [])
        hist = self.history_heuristic

        scored = []
        for mv in moves:
            score = 0
            if tt_move and mv == tt_move:
                score += 10_000_000
            if board.is_capture(mv) or board.gives_check(mv):
                score += 100_000 + self.mvv_lva(board, mv)
            if mv in killers:
                score += 50_000
            score += hist.get((mv.from_square, mv.to_square), 0)
            # prefer promotions
            if mv.promotion:
                score += 150_000 + (mv.promotion * 10)
            scored.append((score, mv))
        scored.sort(key=lambda x: x[0], reverse=True)
        return [m for _, m in scored]

    def store_killer(self, depth: int, move: chess.Move):
        arr = self.killer_moves.setdefault(depth, [])
        if move not in arr:
            arr.insert(0, move)
            if len(arr) > 2:
                arr.pop()

    # --------- Search ---------

    def quiescence(self, board: chess.Board, alpha: int, beta: int, ply: int) -> int:
        stand = self.evaluate(board)
        if stand >= beta:
            return beta
        if alpha < stand:
            alpha = stand

        # Only good captures and checks to avoid horizon effect
        moves = [m for m in board.legal_moves if board.is_capture(m) or board.gives_check(m)]
        moves = self.order_moves(board, moves, None, ply)

        for mv in moves:
            # Delta pruning (skip obviously bad captures)
            if not board.is_capture(mv) and not board.gives_check(mv):
                continue
            board.push(mv)
            score = -self.quiescence(board, -beta, -alpha, ply+1)
            board.pop()

            if score >= beta:
                return beta
            if score > alpha:
                alpha = score
        return alpha

    def negamax(self, board: chess.Board, depth: int, alpha: int, beta: int, ply: int, start_time: float) -> int:
        # Time check
        if time.time() - start_time > self.hard_time_limit:
            return self.evaluate(board)

        key = self.tt_key(board)
        tt_entry = self.tt.get(key)

        if tt_entry and tt_entry.depth >= depth:
            if tt_entry.flag == 0:
                return tt_entry.score
            elif tt_entry.flag == -1:
                alpha = max(alpha, tt_entry.score)
            elif tt_entry.flag == 1:
                beta = min(beta, tt_entry.score)
            if alpha >= beta:
                return tt_entry.score

        if depth <= 0 or board.is_game_over():
            return self.quiescence(board, alpha, beta, ply)

        # Null move pruning
        if depth >= 3 and not board.is_check() and any(board.pieces(pt, board.turn) for pt in [chess.QUEEN, chess.ROOK, chess.BISHOP, chess.KNIGHT]):
            board.push(chess.Move.null())
            score = -self.negamax(board, depth-2, -beta, -beta+1, ply+1, start_time)
            board.pop()
            if score >= beta:
                return score

        # Internal iterative deepening to find a good tt move
        tt_move = tt_entry.move if tt_entry else None

        moves = list(board.legal_moves)
        moves = self.order_moves(board, moves, tt_move, ply)

        best_score = -INFTY
        best_move = None
        original_alpha = alpha

        for i, mv in enumerate(moves):
            board.push(mv)
            # Late move reduction
            new_depth = depth - 1
            if i >= 4 and depth >= 3 and not board.is_capture(mv) and not board.gives_check(mv):
                score = -self.negamax(board, new_depth-1, -alpha-1, -alpha, ply+1, start_time)
            else:
                score = -self.negamax(board, new_depth, -beta, -alpha, ply+1, start_time)
            # PVS re-search
            if score > alpha and score < beta and i > 0:
                score = -self.negamax(board, new_depth, -beta, -alpha, ply+1, start_time)
            board.pop()

            if score > best_score:
                best_score = score
                best_move = mv
            if score > alpha:
                alpha = score
                # good move improves history
                if not board.is_capture(mv):
                    self.history_heuristic[(mv.from_square, mv.to_square)] = self.history_heuristic.get((mv.from_square, mv.to_square), 0) + depth*depth
            if alpha >= beta:
                # store killer on cutoff
                if not board.is_capture(mv):
                    self.store_killer(ply, mv)
                break

        # Store TT
        flag = 0
        if best_score <= original_alpha:
            flag = -1  # alpha
        elif best_score >= beta:
            flag = 1   # beta
        self.tt[key] = TTEntry(depth=depth, score=best_score, flag=flag, move=best_move)

        return best_score

    def search(self, board: chess.Board, max_depth: int = 6, move_time: float = 2.0) -> chess.Move:
        self.soft_time_limit = max(0.5, move_time * 0.9)
        self.hard_time_limit = max(move_time, self.soft_time_limit + 0.2)

        # Try opening book
        if self.book:
            try:
                entries = list(self.book.find_all(board))
                if entries:
                    # choose the highest-weighted entry deterministically
                    best = max(entries, key=lambda e: e.weight)
                    return best.move
            except Exception:
                pass

        start = time.time()
        best_move = None
        best_score = -INFTY

        # Iterative deepening with aspiration windows
        alpha, beta = -INFTY, INFTY
        for depth in range(1, max_depth + 1):
            if time.time() - start > self.soft_time_limit:
                break

            score = -INFTY
            current_best = None
            moves = self.order_moves(board, list(board.legal_moves), None, 0)

            # Aspiration window: narrow window around previous best to speed up
            a, b = (best_score - 50, best_score + 50) if best_move else (alpha, beta)

            for mv in moves:
                if time.time() - start > self.soft_time_limit:
                    break
                board.push(mv)
                val = -self.negamax(board, depth-1, -b, -a, 1, start)
                if val <= a or val >= b:
                    # research with full window
                    val = -self.negamax(board, depth-1, -INFTY, INFTY, 1, start)
                board.pop()

                if val > score:
                    score = val
                    current_best = mv
                if val > a:
                    a = val

            if current_best is not None:
                best_move = current_best
                best_score = score

            # Hard stop
            if time.time() - start > self.hard_time_limit:
                break

        if best_move is None:
            # fallback
            best_move = random.choice(list(board.legal_moves))
        return best_move

def get_player_color():
    while True:
        choice = input("Do you want to play as (W)hite or (B)lack? ").upper()
        if choice in ['W', 'WHITE']:
            return chess.WHITE
        elif choice in ['B', 'BLACK']:
            return chess.BLACK
        print("Please enter 'W' for White or 'B' for Black")

SYMBOLS = {
    'r': '♖', 'n': '♘', 'b': '♗', 'q': '♕', 'k': '♔', 'p': '♙',
    'R': '♜', 'N': '♞', 'B': '♝', 'Q': '♛', 'K': '♚', 'P': '♟',
    None: '·'
}

def print_board(board: chess.Board, player_color: bool):
    if player_color == chess.WHITE:
        for rank in range(7, -1, -1):
            print(' ' + ' '.join(
                SYMBOLS[board.piece_at(chess.square(file, rank)).symbol() if board.piece_at(chess.square(file, rank)) else None]
                for file in range(8)
            ))
    else:
        for rank in range(8):
            print(' ' + ' '.join(
                SYMBOLS[board.piece_at(chess.square(7-file, rank)).symbol() if board.piece_at(chess.square(7-file, rank)) else None]
                for file in range(8)
            ))
    print()

def play_chess(book_path: str | None = None, max_depth: int = 8, move_time: float = 2.0):
    ai = StrongChessAI(book_path)
    board = chess.Board()

    print("\nWelcome to Chess against AI!")
    player_color = get_player_color()
    print(f"\nYou are playing as {'WHITE' if player_color == chess.WHITE else 'BLACK'}")
    print("Type 'Quit' during your turn to exit.\n")

    if player_color == chess.BLACK:
        print("AI (White) moves first!")

    while not board.is_game_over():
        print_board(board, player_color)

        if board.turn == player_color:
            while True:
                move_uci = input("Your move (e.g. 'e2e4'), or 'Quit': ").strip().lower()
                if move_uci == 'quit':
                    print("\nThanks for playing! Goodbye!\n")
                    return
                try:
                    move = chess.Move.from_uci(move_uci)
                    if move in board.legal_moves:
                        break
                    print("Illegal move!")
                except Exception:
                    print("Invalid input (use format like 'e2e4' or 'Quit')")
            board.push(move)
        else:
            print("AI is thinking...")
            start_time = time.time()
            move = ai.search(board, max_depth=max_depth, move_time=move_time)  # Increase max_depth for strength
            board.push(move)
            print(f"AI plays: {move.uci()} (in {time.time()-start_time:.2f}s)")

    # Game over
    print("\nGame over!")
    print("Final position:\n")
    print_board(board, player_color)
    result = board.result()
    if result == "1-0":
        print("White wins!\n")
    elif result == "0-1":
        print("Black wins!\n")
    else:
        print("It's a draw!\n")

if __name__ == "__main__":
    play_chess(book_path="Titans.bin", max_depth=10, move_time=2.5)
