# Chess AI for the Eve Project

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/github/license/dolovesv/chess_ai)](LICENSE)
[![Tests](https://img.shields.io/badge/tests-passing-brightgreen.svg)](chess_ai/tests/)

A standalone chess AI built around the Stockfish engine designed to play on [Lichess](https://lichess.org/), created specifically for **Eve**, an AI VTuber. This sophisticated AI integrates with the Lichess platform, allowing for dynamic skill adjustments and human-like gameplay that ranges from casual to expert level.

## 📋 Table of Contents

- [Purpose](#-purpose)
- [Quick Start](#-quick-start)
- [Features](#-features)
- [Technical Architecture](#-technical-architecture)
- [Installation](#-installation)
- [Usage](#-usage)
- [Development](#-development)
- [Documentation](#-documentation)
- [References](#-references)

## 🎯 Purpose

Eve uses this AI module to:

- Play chess live on Twitch or YouTube against viewers and guests
- Dynamically adjust playing strength during games (800-2500 Elo rating)
- Make occasional human-like mistakes (blunders) to simulate natural gameplay
- Demonstrate moments of brilliance with unexpected powerful moves
- Provide expert analysis and commentary on positions

This module functions as a standalone chess AI but is primarily designed to be integrated with the main [Eve project (Private Repository)].

## 🚀 Quick Start

For those who want to get up and running quickly:

```bash
# Clone the repository
git clone https://github.com/dolovesv/chess_ai.git
cd chess_ai

# Install dependencies
pip install -r requirements.txt

# Set up your Lichess API token
echo "LICHESS_API_TOKEN=your_token_here" > .env

# Run the bot with default settings
python run_lichess_bot.py
```

## 🎮 Features

### 🌐 Lichess.org Integration

- Complete Lichess API integration for online play
- Bot account management
- Challenge acceptance and game management
- Real-time game streaming and move execution

### ♟️ Advanced Chess Engine

- Stockfish integration with personality-based move selection
- Customizable playing styles (aggressive, defensive, creative, positional, solid)
- Opening book knowledge with personality-preferred openings
- Dynamic evaluation and decision making

### 🧠 Human-like Gameplay

- ELO rating range from 800 (beginner) to 2500+ (expert)
- Deliberate introduction of human-like errors based on skill level
- Occasional brilliant moves that exceed the set skill level
- Naturalistic move selection with varied play styles

### 🎭 Personality System

- Five distinct chess personalities affecting move selection
- Personality-specific commentary and evaluation
- Opening preferences based on personality traits
- Adaptable confidence levels that affect play style

### 📊 Analysis and Evaluation

- Real-time position evaluation
- Move confidence metrics
- Game state tracking and management
- Detailed move explanation and commentary

## 🏗 Technical Architecture

The Chess AI is built with a modular architecture consisting of several key components:

### Core Components

- **`ai_engine.py`**: Core chess AI implementing minimax with alpha-beta pruning
- **`lichess_bot.py`**: Handles all Lichess.org API communication
- **`bot_runner.py`**: Connects the AI engine to the Lichess platform
- **`stockfish_adapter.py`**: Integrates with Stockfish and adds personality-based move selection
- **`state_manager.py`**: Manages the chess board state and position representation
- **`evaluation.py`**: Evaluates chess positions
- **`move_generator.py`**: Generates legal moves from a given position

### Integration Flow

1. The `bot_runner.py` serves as the entry point, initializing the AI engine and Lichess bot
2. `lichess_bot.py` handles all API interactions with Lichess.org
3. When it's the bot's turn, the position is converted to the internal representation
4. The `ai_engine.py` or `stockfish_adapter.py` selects the best move
5. The move is executed via the Lichess API

### State Management

The system uses a custom `ChessState` representation internally, with conversion utilities for the python-chess library and Lichess API formats. This allows for consistent state management across different components.

## 📥 Installation

### Prerequisites

1. **Python 3.8+** - The project is built with Python 3.8 or newer
2. **Stockfish Chess Engine** - Required for the AI

#### Installing Stockfish:

**macOS (using Homebrew):**

```bash
brew install stockfish
```

**Ubuntu/Debian:**

```bash
sudo apt-get install stockfish
```

**Windows:**

- Download from https://stockfishchess.org/download/
- Extract the executable to a known location
- Add to PATH or specify the path in the code

Verify installation:

```bash
stockfish --version
```

### Setting Up the Project

1. Clone the repository:

```bash
git clone https://github.com/dolovesv/chess_ai.git
cd chess_ai
```

2. Create and activate a virtual environment:

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:

```bash
pip install -r requirements.txt
```

4. Create a `.env` file with your Lichess API token:

```
LICHESS_API_TOKEN=your_lichess_api_token_here
```

### Lichess Bot Account Setup

To use this project with Lichess, you need a Lichess BOT account:

1. Create a new Lichess account (must not have played any games)
2. Generate an API token at https://lichess.org/account/oauth/token
3. Run the setup utility:

```bash
python -m chess_ai.lichess_bot setup
```

## 🚀 Usage

### Running the Bot

Basic usage with default settings:

```bash
python run_lichess_bot.py
```

With custom difficulty (1-5) and time limit:

```bash
python run_lichess_bot.py --difficulty=3 --time-limit=5
```

### Command Line Arguments

- `--difficulty` (1-5): AI difficulty level:
  - 1: Beginner (~800 ELO)
  - 3: Medium (~1500 ELO) (default)
  - 5: Expert (~2500 ELO)
- `--time-limit` (seconds): Time limit for move calculation (default: 5.0s)
- `--verbose`: Enable verbose logging

### Configuration Options

The AI behavior can be customized through:

1. **Personality:** Change the default personality in the code:

   - `aggressive`: Prefers attacking moves and sacrifices
   - `defensive`: Prefers solid positions and safety
   - `creative`: Plays unusual and surprising moves
   - `solid`: Plays principled, theoretically sound moves (default)
   - `positional`: Focuses on long-term positional advantages

2. **Custom Opening Books:** Provide a custom opening book JSON file

3. **Environment Variables:**
   - `LICHESS_API_TOKEN`: Your Lichess API token

### Running Tests

Execute the test suite:

```bash
python -m unittest discover chess_ai/tests
```

## 💻 Development

### Project Structure

```
chess_ai/
├── __init__.py          # Package initialization
├── ai_engine.py         # Chess AI core (minimax with alpha-beta pruning)
├── bot_runner.py        # Connects AI engine to Lichess API
├── evaluation.py        # Position evaluation functions
├── game_controller.py   # Game state control and management
├── lichess_bot.py       # Lichess.org API communication
├── move_generator.py    # Legal move generation
├── state_manager.py     # Chess state representation
├── stockfish_adapter.py # Stockfish integration with personality
├── demo/                # Demo applications
└── tests/               # Unit tests
    ├── test_chess_ai.py
    ├── test_stockfish_adapter.py
    └── test_data/       # Test data files
```

### Logs

Game logs are stored in the `logs/` directory with detailed information about bot actions, game states, and API interactions.

### Contributing

Contributions are welcome! Please follow these steps:

1. Fork the repository
2. Create a feature branch: `git checkout -b feature-name`
3. Commit your changes: `git commit -am 'Add some feature'`
4. Push to the branch: `git push origin feature-name`
5. Submit a pull request

### License

This project is licensed under the terms specified in the `LICENSE` file.

## 📚 Documentation

### API Reference

Key classes and their primary methods:

#### ChessAI (ai_engine.py)

- `get_best_move(state)`: Returns the best move for the current position
- `set_difficulty(difficulty)`: Sets the AI difficulty level (1-5)
- `set_time_limit(seconds)`: Sets the time limit for move calculation

#### LichessBot (lichess_bot.py)

- `start_bot_loop()`: Starts the main event loop for Lichess integration
- `accept_challenge(challenge_id)`: Accepts a challenge from another player
- `make_move(game_id, move)`: Makes a move in an ongoing game

#### StockfishAdapter (stockfish_adapter.py)

- `set_personality(personality)`: Sets the AI's chess personality
- `set_elo_rating(elo)`: Sets the approximate playing strength
- `get_move(fen, moves)`: Gets a move with personality and commentary

### Environment Variables

- `LICHESS_API_TOKEN`: Authentication token for Lichess API (required)

### Troubleshooting

Common issues and solutions:

**Stockfish not found:**

- Ensure Stockfish is installed and in your PATH
- Specify the direct path to the Stockfish executable

**Lichess API connection issues:**

- Verify your API token is valid
- Ensure your bot account has been properly set up

**Game handling errors:**

- Check the logs for detailed error information

For detailed logs and debugging, use the `--verbose` flag when running the bot.

## 🔗 References

- [Lichess API Documentation](https://lichess.org/api)
- [Stockfish Chess Engine](https://stockfishchess.org/)
- [Python Chess Library](https://python-chess.readthedocs.io/)
- [Berserk (Lichess API Client)](https://berserk.readthedocs.io/)
