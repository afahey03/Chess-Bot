import chess
import chess.pgn
import torch
import zstandard
import numpy as np

PIECE_TO_CHANNEL = {
    'P': 0, 'N': 1, 'B': 2, 'R': 3, 'Q': 4, 'K': 5,
    'p': 6, 'n': 7, 'b': 8, 'r': 9, 'q': 10, 'k': 11,
}

RESULT_TO_VALUE = {'1-0': 1.0, '0-1': -1.0, '1/2-1/2': 0.0}

def board_to_tensor(board: chess.Board) -> torch.Tensor:
    """
    Converts a chess.Board object to a (12, 8, 8) tensor.
    """
    tensor = torch.zeros(12, 8, 8)
    for sq in chess.SQUARES:
        piece = board.piece_at(sq)
        if piece:
            channel = PIECE_TO_CHANNEL[piece.symbol()]
            rank, file = chess.square_rank(sq), chess.square_file(sq)
            tensor[channel, rank, file] = 1
    return tensor

def process_game(game):
    """
    Generator function that yields (tensor, result_value) pairs for each
    position in a game.
    """
    result = game.headers.get("Result")
    if result not in RESULT_TO_VALUE:
        return

    result_value = RESULT_TO_VALUE[result]
    board = game.board()

    for move in game.mainline_moves():
        board.push(move)
        if board.fullmove_number > 10:
            tensor = board_to_tensor(board)
            yield tensor, result_value

def parse_database(pgn_file_path, max_games=None):
    """
    Parses a PGN database and yields training data.
    """
    with open(pgn_file_path, 'rb') as f:
        dctx = zstandard.ZstdDecompressor(pgn_file_path)
        with dctx.stream_reader(f) as reader:
            pgn = chess.pgn.read_game(reader)
            game_count = 0
            while True:
                if max_games and game_count >= max_games:
                    break
                try:
                    game = chess.pgn.read_game(pgn)
                    if game is None:
                        break
                    yield from process_game(game)
                    game_count += 1
                except (ValueError, IndexError) as e:
                    print(f"Skipping a malformed game. Error: {e}")
                    continue