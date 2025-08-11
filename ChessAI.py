# Aidan Fahey
# 6/22/2025 - 6/23/2025
# AI Chess Game
# I have no idea what rating this AI would be

import chess
import chess.polyglot
import math
import random
import time

class ChessAI:
    def __init__(self, book_path):
        self.book = chess.polyglot.open_reader(book_path)
    
    def evaluate_board(self, board):
        # Game outcome evaluations
        if board.is_checkmate():
            return -99999 if board.turn else 99999
        if board.is_stalemate() or board.is_insufficient_material():
            return 0
        
        # Piece values (centipawns)
        piece_values = {
            chess.PAWN: 100,
            chess.KNIGHT: 320,
            chess.BISHOP: 330,
            chess.ROOK: 500,
            chess.QUEEN: 900,
            chess.KING: 20000
        }

        pawn_table = [
             0,   0,   0,   0,   0,   0,   0,   0,
            50,  50,  50,  50,  50,  50,  50,  50,
            10,  10,  20,  30,  30,  20,  10,  10,
             5,   5,  10,  25,  25,  10,   5,   5,
             0,   0,   0,  20,  20,   0,   0,   0,
             5,  -5, -10,   0,   0, -10,  -5,   5,
             5,  10,  10, -20, -20,  10,  10,   5,
             0,   0,   0,   0,   0,   0,   0,   0
        ]

        knight_table = [
            -50, -40, -30, -30, -30, -30, -40, -50,
            -40, -20,   0,   0,   0,   0, -20, -40,
            -30,   0,  10,  15,  15,  10,   0, -30,
            -30,   5,  15,  20,  20,  15,   5, -30,
            -30,   0,  15,  20,  20,  15,   0, -30,
            -30,   5,  10,  15,  15,  10,   5, -30,
            -40, -20,   0,   5,   5,   0, -20, -40,
            -50, -40, -30, -30, -30, -30, -40, -50
        ]

        bishop_table = [
            -20, -10, -10, -10, -10, -10, -10, -20,
            -10,   0,   0,   0,   0,   0,   0, -10,
            -10,   0,   5,  10,  10,   5,   0, -10,
            -10,   5,   5,  10,  10,   5,   5, -10,
            -10,   0,  10,  10,  10,  10,   0, -10,
            -10,  10,  10,  10,  10,  10,  10, -10,
            -10,   5,   0,   0,   0,   0,   5, -10,
            -20, -10, -10, -10, -10, -10, -10, -20
        ]

        rook_table = [
             0,   0,   0,   0,   0,   0,   0,   0,
             5,  10,  10,  10,  10,  10,  10,   5,
            -5,   0,   0,   0,   0,   0,   0,  -5,
            -5,   0,   0,   0,   0,   0,   0,  -5,
            -5,   0,   0,   0,   0,   0,   0,  -5,
            -5,   0,   0,   0,   0,   0,   0,  -5,
            -5,   0,   0,   0,   0,   0,   0,  -5,
             0,   0,   0,   5,   5,   0,   0,   0
        ]

        king_table = [
            -30, -40, -40, -50, -50, -40, -40, -30,
            -30, -40, -40, -50, -50, -40, -40, -30,
            -30, -40, -40, -50, -50, -40, -40, -30,
            -30, -40, -40, -50, -50, -40, -40, -30,
            -20, -30, -30, -40, -40, -30, -30, -20,
            -10, -20, -20, -20, -20, -20, -20, -10,
             20,  20,   0,   0,   0,   0,  20,  20,
             20,  30,  10,   0,   0,  10,  30,  20
        ]

        score = 0
        white_pawns = set()
        black_pawns = set()
        white_bishops = 0
        black_bishops = 0

        # Material and piece-square tables
        for square in chess.SQUARES:
            piece = board.piece_at(square)
            if not piece:
                continue
                
            # Flip square for black pieces
            adjusted_square = square if piece.color == chess.WHITE else chess.square_mirror(square)
            value = piece_values[piece.piece_type]
            
            # Add piece-square table value
            if piece.piece_type == chess.PAWN:
                value += pawn_table[adjusted_square]
                if piece.color == chess.WHITE:
                    white_pawns.add(square)
                else:
                    black_pawns.add(square)
            elif piece.piece_type == chess.KNIGHT:
                value += knight_table[adjusted_square]
            elif piece.piece_type == chess.BISHOP:
                value += bishop_table[adjusted_square]
                if piece.color == chess.WHITE:
                    white_bishops += 1
                else:
                    black_bishops += 1
            elif piece.piece_type == chess.ROOK:
                value += rook_table[adjusted_square]
            elif piece.piece_type == chess.KING:
                value += king_table[adjusted_square]
            
            score += value if piece.color == chess.WHITE else -value

        # Pawn structure evaluation (simplified)
        white_pawn_files = [chess.square_file(p) for p in white_pawns]
        black_pawn_files = [chess.square_file(p) for p in black_pawns]
        
        # Doubled pawn penalty
        for file in range(8):
            white_count = white_pawn_files.count(file)
            black_count = black_pawn_files.count(file)
            if white_count > 1:
                score -= 20 * (white_count - 1)
            if black_count > 1:
                score += 20 * (black_count - 1)
        
        # Isolated pawn penalty (simplified)
        for pawn in white_pawns:
            file = chess.square_file(pawn)
            if (file == 0 or (file - 1) not in white_pawn_files) and \
               (file == 7 or (file + 1) not in white_pawn_files):
                score -= 25
                
        for pawn in black_pawns:
            file = chess.square_file(pawn)
            if (file == 0 or (file - 1) not in black_pawn_files) and \
               (file == 7 or (file + 1) not in black_pawn_files):
                score += 25
        
        # Bishop pair bonus
        if white_bishops >= 2:
            score += 30
        if black_bishops >= 2:
            score -= 30
        
        # Mobility (quicker calculation)
        mobility_weight = 0.5
        current_turn = board.turn
        board.turn = chess.WHITE
        white_mobility = board.legal_moves.count()
        board.turn = chess.BLACK
        black_mobility = board.legal_moves.count()
        board.turn = current_turn
        score += (white_mobility - black_mobility) * mobility_weight
        
        # Tempo bonus
        score += 10 if board.turn == chess.WHITE else -10
        
        return score
    
    def quiescence_search(self, board, alpha, beta, color):
        stand_pat = self.evaluate_board(board) * (1 if color == chess.WHITE else -1)
        
        if stand_pat >= beta:
            return beta
        if alpha < stand_pat:
            alpha = stand_pat
            
        # Only look at captures
        for move in board.legal_moves:
            if not board.is_capture(move):
                continue
                
            board.push(move)
            score = -self.quiescence_search(board, -beta, -alpha, not color)
            board.pop()
            
            if score >= beta:
                return beta
            if score > alpha:
                alpha = score
                
        return alpha
    
    def alpha_beta(self, board, depth, alpha, beta, maximizing_player, start_time, time_limit=2.0):
        if depth == 0 or board.is_game_over():
            return self.quiescence_search(board, alpha, beta, maximizing_player)
            
        # Time check
        if time.time() - start_time > time_limit:
            return 0  # Return neutral value if time runs out
            
        # Move ordering - captures first
        legal_moves = sorted(board.legal_moves, 
                            key=lambda m: (board.is_capture(m), self.evaluate_move(board, m)), 
                            reverse=maximizing_player)
        
        if maximizing_player:
            value = -math.inf
            for move in legal_moves:
                board.push(move)
                value = max(value, self.alpha_beta(board, depth-1, alpha, beta, False, start_time, time_limit))
                board.pop()
                alpha = max(alpha, value)
                if alpha >= beta:
                    break  # Beta cutoff
            return value
        else:
            value = math.inf
            for move in legal_moves:
                board.push(move)
                value = min(value, self.alpha_beta(board, depth-1, alpha, beta, True, start_time, time_limit))
                board.pop()
                beta = min(beta, value)
                if alpha >= beta:
                    break  # Alpha cutoff
            return value
    
    def evaluate_move(self, board, move):
        if board.is_capture(move):
            # Use MVV-LVA (Most Valuable Victim - Least Valuable Aggressor)
            victim = board.piece_at(move.to_square)
            aggressor = board.piece_at(move.from_square)
            if victim and aggressor:
                return victim.piece_type * 100 - aggressor.piece_type
        return 0
    
    def get_ai_move(self, board, depth, time_limit):
        start_time = time.time()
        
        # Try book move first
        if self.book:
            try:
                entries = list(self.book.find_all(board))
                if entries:
                    total_weight = sum(entry.weight for entry in entries)
                    r = random.uniform(0, total_weight)
                    cumulative = 0
                    for entry in entries:
                        cumulative += entry.weight
                        if r <= cumulative:
                            return entry.move
            except:
                pass
        
        # If no book move, perform search
        best_move = None
        best_value = -math.inf if board.turn == chess.WHITE else math.inf
        
        # Iterative deepening
        current_depth = 1
        while current_depth <= depth and time.time() - start_time < time_limit:
            for move in board.legal_moves:
                board.push(move)
                value = self.alpha_beta(
                    board, 
                    current_depth-1, 
                    -math.inf, 
                    math.inf, 
                    board.turn == chess.BLACK,
                    start_time,
                    time_limit
                )
                board.pop()
                
                if board.turn == chess.WHITE and value > best_value:
                    best_value = value
                    best_move = move
                elif board.turn == chess.BLACK and value < best_value:
                    best_value = value
                    best_move = move
            
            current_depth += 1
        
        # If we didn't find a move (shouldn't happen), pick random legal move
        if not best_move:
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

def print_board(board, player_color):
    symbols = {
        'r': '♖', 'n': '♘', 'b': '♗', 'q': '♕', 'k': '♔', 'p': '♙',
        'R': '♜', 'N': '♞', 'B': '♝', 'Q': '♛', 'K': '♚', 'P': '♟',
        None: '·'
    }
    
    if player_color == chess.WHITE:
        for rank in range(7, -1, -1):
            print(' ' + ' '.join(
                symbols[board.piece_at(chess.square(file, rank)).symbol() if board.piece_at(chess.square(file, rank)) else None]
                for file in range(8)
            ))
    else:
        for rank in range(8):
            print(' ' + ' '.join(
                symbols[board.piece_at(chess.square(7-file, rank)).symbol() if board.piece_at(chess.square(7-file, rank)) else None]
                for file in range(8)
            ))
    print()

def play_chess(book_path):

    ai = ChessAI(book_path)
    board = chess.Board()

    print("\nWelcome to Chess against AI!")
    player_color = get_player_color()
    print(f"\nYou are playing as {'WHITE' if player_color == chess.WHITE else 'BLACK'}")
    print("Type 'Quit' during your turn to exit.\n")

    board.turn = chess.WHITE
    
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
                except:
                    print("Invalid input (use format like 'e2e4' or 'Quit')")
            board.push(move)
        else:
            print("AI is thinking...")
            start_time = time.time()
            move = ai.get_ai_move(board, depth=4, time_limit=10.0) # Change depth and time_limit as needed
            board.push(move)
            print(f"AI plays: {move.uci()} (in {time.time()-start_time:.1f}s)")
    
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
    play_chess(book_path="Titans.bin") # Change book_path to desired book