from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import Optional
import chess
import logging
from datetime import datetime

from main import ChessAI

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Chess AI API",
    description="API for playing chess against an AI opponent",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

chess_ai = ChessAI(book_path="Titans.bin")

class MoveRequest(BaseModel):
    board: str 
    depth: Optional[int] = 6
    moveTime: Optional[float] = 2.0

class MoveResponse(BaseModel):
    move: str 
    evaluation: Optional[float] = None
    thinking_time: float

class BoardStateRequest(BaseModel):
    board: str

class BoardStateResponse(BaseModel):
    is_check: bool
    is_checkmate: bool
    is_stalemate: bool
    is_insufficient_material: bool
    is_game_over: bool
    legal_moves: list[str]
    turn: str 

class NewGameRequest(BaseModel):
    player_color: str  
    difficulty: Optional[str] = 'medium' 

class ValidateMoveRequest(BaseModel):
    board: str 
    move: str 

class ValidateMoveResponse(BaseModel):
    is_valid: bool
    resulting_fen: Optional[str] = None
    is_capture: bool = False
    is_check: bool = False
    is_checkmate: bool = False
    san_notation: Optional[str] = None


@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "message": "Chess AI API Server",
        "version": "1.0.0",
        "endpoints": {
            "/api/get-move": "Get AI move for a position",
            "/api/board-state": "Get current board state information",
            "/api/validate-move": "Validate a move and get resulting position",
            "/api/new-game": "Start a new game",
            "/api/legal-moves": "Get all legal moves for a position",
            "/docs": "API documentation"
        }
    }

@app.post("/api/get-move", response_model=MoveResponse)
async def get_ai_move(request: MoveRequest):
    """
    Get the AI's move for a given board position.
    
    - **board**: FEN string representing the current board position
    - **depth**: Search depth (4-10, higher = stronger but slower)
    - **moveTime**: Maximum time in seconds for the AI to think
    """
    try:
        board = chess.Board(request.board)
        
        if board.is_game_over():
            raise HTTPException(status_code=400, detail="Game is already over")
        
        depth = request.depth
        move_time = request.moveTime
        
        import time
        start_time = time.time()
        
        logger.info(f"AI thinking: depth={depth}, time_limit={move_time}s")
        move = chess_ai.search(board, max_depth=depth, move_time=move_time)
        
        thinking_time = time.time() - start_time
        
        board.push(move)
        evaluation = chess_ai.evaluate(board) / 100
        board.pop()
        
        logger.info(f"AI move: {move.uci()} (eval: {evaluation:.2f}, time: {thinking_time:.2f}s)")
        
        return MoveResponse(
            move=move.uci(),
            evaluation=evaluation,
            thinking_time=round(thinking_time, 2)
        )
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid FEN string: {str(e)}")
    except Exception as e:
        logger.error(f"Error getting AI move: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.post("/api/board-state", response_model=BoardStateResponse)
async def get_board_state(request: BoardStateRequest):
    """
    Get comprehensive information about the current board state.
    
    - **board**: FEN string representing the current board position
    """
    try:
        board = chess.Board(request.board)
        
        return BoardStateResponse(
            is_check=board.is_check(),
            is_checkmate=board.is_checkmate(),
            is_stalemate=board.is_stalemate(),
            is_insufficient_material=board.is_insufficient_material(),
            is_game_over=board.is_game_over(),
            legal_moves=[move.uci() for move in board.legal_moves],
            turn='white' if board.turn == chess.WHITE else 'black'
        )
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid FEN string: {str(e)}")

@app.post("/api/validate-move", response_model=ValidateMoveResponse)
async def validate_move(request: ValidateMoveRequest):
    """
    Validate a move and get the resulting board position.
    
    - **board**: FEN string representing the current board position
    - **move**: Move in UCI notation (e.g., 'e2e4')
    """
    try:
        board = chess.Board(request.board)
        
        try:
            move = chess.Move.from_uci(request.move)
        except:
            return ValidateMoveResponse(is_valid=False)
        
        if move not in board.legal_moves:
            return ValidateMoveResponse(is_valid=False)
        
        is_capture = board.is_capture(move)
        san_notation = board.san(move)
        
        board.push(move)
        
        return ValidateMoveResponse(
            is_valid=True,
            resulting_fen=board.fen(),
            is_capture=is_capture,
            is_check=board.is_check(),
            is_checkmate=board.is_checkmate(),
            san_notation=san_notation
        )
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid FEN string: {str(e)}")

@app.get("/api/legal-moves")
async def get_legal_moves(fen: str):
    """
    Get all legal moves for a given position.
    
    - **fen**: FEN string representing the board position
    """
    try:
        board = chess.Board(fen)
        
        moves = []
        for move in board.legal_moves:
            move_info = {
                "uci": move.uci(),
                "san": board.san(move),
                "from_square": chess.square_name(move.from_square),
                "to_square": chess.square_name(move.to_square),
                "is_capture": board.is_capture(move),
                "is_check": board.gives_check(move)
            }
            moves.append(move_info)
        
        return {
            "legal_moves": moves,
            "count": len(moves)
        }
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid FEN string: {str(e)}")

@app.post("/api/new-game")
async def new_game(request: NewGameRequest):
    """
    Start a new game and get initial board state.
    
    - **player_color**: 'white' or 'black'
    - **difficulty**: 'easy', 'medium', 'hard', or 'expert'
    """
    if request.player_color not in ['white', 'black']:
        raise HTTPException(status_code=400, detail="Player color must be 'white' or 'black'")
    
    difficulty_map = {
        'easy': {'depth': 4, 'time': 1.0},
        'medium': {'depth': 6, 'time': 2.0},
        'hard': {'depth': 8, 'time': 3.0},
        'expert': {'depth': 10, 'time': 5.0}
    }
    
    difficulty = request.difficulty if request.difficulty in difficulty_map else 'medium'
    settings = difficulty_map[difficulty]
    
    board = chess.Board()
    
    response = {
        "fen": board.fen(),
        "player_color": request.player_color,
        "difficulty": difficulty,
        "settings": settings,
        "ai_moves_first": request.player_color == 'black'
    }
    
    if request.player_color == 'black':
        move = chess_ai.search(board, max_depth=settings['depth'], move_time=settings['time'])
        board.push(move)
        response["ai_first_move"] = move.uci()
        response["fen"] = board.fen()
    
    return response

@app.get("/api/evaluate")
async def evaluate_position(fen: str):
    """
    Get the AI's evaluation of a position.
    
    - **fen**: FEN string representing the board position
    """
    try:
        board = chess.Board(fen)
        
        # Get raw evaluation
        eval_score = chess_ai.evaluate(board)
        
        # Convert to pawns (centipawns / 100)
        eval_pawns = eval_score / 100
        
        # Determine advantage
        if abs(eval_pawns) < 0.2:
            advantage = "equal"
        elif eval_pawns > 0:
            advantage = "white"
        else:
            advantage = "black"
        
        return {
            "evaluation": round(eval_pawns, 2),
            "centipawns": eval_score,
            "advantage": advantage,
            "is_mate_score": abs(eval_score) >= 10000000 - 1000
        }
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid FEN string: {str(e)}")

@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat()
    }

app.mount("/static", StaticFiles(directory="static"), name="static")

if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info"
    )