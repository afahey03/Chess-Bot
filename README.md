# ♟️ Chess Bot

A powerful chess engine with a web interface. Challenge yourself against an intelligent AI opponent with adjustable difficulty levels!

![Chess AI](https://img.shields.io/badge/Chess-AI-blue)
![Python](https://img.shields.io/badge/Python-3.8+-green)
![License](https://img.shields.io/badge/License-MIT-yellow)

## 🎮 Features

- **Chess AI** with advanced algorithms:
  - Negamax search with alpha-beta pruning
  - Iterative deepening
  - Quiescence search
  - Move ordering with MVV-LVA
  - Transposition tables
  - Null move pruning
  - Opening book support
  
- **Web Interface**:
  - Clean, modern design
  - Drag-and-drop piece movement
  - Move highlighting
  - Captured pieces display
  - Move history in standard notation
  - Check/checkmate indicators
  
- **Customizable Gameplay**:
  - 4 difficulty levels (Easy, Medium, Hard, Expert)
  - Adjustable AI thinking time
  - Play as White or Black
  - Board flip option

## 🚀 Quick Start

### Prerequisites

- Python 3.8 or higher
- pip (Python package manager)
- Modern web browser (Chrome, Firefox, Safari, Edge)

### Installation

1. **Clone the repository**
```bash
git clone https://github.com/afahey03/Chess-Bot.git
cd Chess-Bot
```

2. **Set up Python virtual environment**
```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

### Running the Game

1. **Start the API server**
```bash
python server.py
```
The server will start on `http://localhost:8000`

2. **Open the game in your browser**
   
   Option A: Open the HTML file directly
   - Navigate to the project folder
   - Open `index.html` in your web browser
   
   Option B: Serve through the API (if configured)
   - Visit `http://localhost:8000/static/index.html`

3. **Start playing!**
   - Choose your color (White or Black)
   - Click a piece to select it
   - Click a highlighted square to move
   - Adjust difficulty in the settings panel

## 🎯 How to Play

### Basic Controls
- **Select a piece**: Click on any of your pieces
- **Move**: Click on a highlighted square to move the selected piece
- **Deselect**: Click elsewhere or press ESC
- **New Game**: Click the "New Game" button
- **Flip Board**: Click "Flip Board" to rotate the view

### Difficulty Levels
- **Easy** (Depth 4): Good for beginners
- **Medium** (Depth 6): Balanced challenge
- **Hard** (Depth 8): Strong opponent
- **Expert** (Depth 10): Maximum strength

## 🛠️ Development

### Running in Development Mode

```bash
# Start server with auto-reload
uvicorn server:app --reload --host 0.0.0.0 --port 8000
```

### API Documentation

Visit `http://localhost:8000/docs` for interactive API documentation (Swagger UI)

### Available API Endpoints

- `POST /api/get-move` - Get AI move for a position
- `POST /api/board-state` - Get current board state
- `POST /api/validate-move` - Validate a move
- `POST /api/new-game` - Start a new game
- `GET /api/legal-moves` - Get all legal moves
- `GET /api/evaluate` - Get position evaluation

## 🐛 Troubleshooting

### Common Issues

**Issue: "Python not found"**
- Make sure Python 3.8+ is installed: `python --version`
- Try using `python3` instead of `python`

**Issue: "Module not found" errors**
- Ensure virtual environment is activated
- Reinstall requirements: `pip install -r requirements.txt`

**Issue: AI not responding**
- Check if server is running: `http://localhost:8000/api/health`
- Check browser console for errors (F12)
- Ensure CORS is not blocked by browser extensions

**Issue: Opening book not working**
- Ensure `Titans.bin` is in the project root directory
- The AI works without it but plays better openings with it

## 🎮 Playing Without Installation

If you just want to play without the AI:
1. Open `index.html` directly in your browser
2. The game will work with random moves instead of AI moves
3. Perfect for playing with a friend locally!

## 📊 Performance

The AI strength depends on:
- **Search depth**: Higher = stronger but slower
- **Time limit**: More time = better moves
- **Opening book**: Improves opening play
- **Hardware**: Faster CPU = quicker responses

Typical performance:
- Easy mode: ~1 second per move
- Expert mode: 3-5 seconds per move

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- Chess piece Unicode symbols
- python-chess library for chess logic
- FastAPI for the backend server
- Polyglot opening book format

---

**Enjoy playing chess! ♟️**
---
**I am having some difficulties pushing changes to this repo, sadly might have to give up on it for a while**
