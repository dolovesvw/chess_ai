---

# Chess Ai for the Eve Project

This is a standalone chess AI built around the Stockfish engine, designed for use by **Eve**, an AI VTuber that I am making. The goal of this project is to allow Eve to play entertaining, fair, and challenging games of chess against human players and show a range of skill levels in her moves.

## 🎯 Purpose

Eve will use this AI module to:

- Play chess live on Twitch or YouTube.
- Compete against viewers or guests.
- Adjust her strength dynamically during the game (800, 1500, 2500 Elo).
- Occasionally make human-like mistakes (blunders) and brilliant moves to simulate natural gameplay and unpredictability.

This module is intended to be integrated into the main [Eve project (Private Repository)] but can also be used as a standalone chess AI.

---

## 🧠 Features

- ✅ Based on the Stockfish chess engine.
- ✅ Adjustable play strength (800, 1500, 2500 Elo).
- ✅ Configurable randomness to simulate human play (blunders, inaccuracies, brilliancies).
- ✅ Simple API to plug into Eve's main codebase or other bots.
- ✅ Works with UCI-compatible interfaces.

---

## 🛠️ Installation

1. **Clone the repository:**

   ```bash
   git clone https://github.com/your-username/eve-chess-ai.git
   cd eve-chess-ai
   ```

2. Download Stockfish:

- [Official Stockfish releases](https://stockfishchess.org/download/)
- Place the Stockfish binary in the engines/ folder and make sure it's executable.

3. Install dependencies:

```bash
pip install -r requirements.txt
```

To run use

```
source venv/bin/activate && python3 -c "from chess_ai.bot_runner import LichessBotRunner; bot = LichessBotRunner(); bot.start()"
```

---

## 🔧 Configuration

You can configure:

- Elo strength: Alters depth and evaluation parameters.
- Blunder chance: Introduces deliberate mistakes.
- Move randomness: Slight variability to simulate non-deterministic play.
- All settings are managed via a config.yaml file or passed at runtime.

---

## 📁 Project Structure

```bash

```

---

## 🧪 Development

- Python 3.8+
- Stockfish 17+
- Unit tests can be run with:

```bash
pytest
```

---

## 📜 License

Apache Commons 2.0 License. See LICENSE for more details.

### 🤖 About Eve

This chess module is part of Eve, a modular AI VTuber designed to entertain, engage, and play games with audiences on Twitch and YouTube.

### 📬 Contributing

Pull requests, feedback, and feature requests are welcome (I DID NOT MAKE THEY WORK YET SO PLEASE HOLD ON BEFORE YOU DO THAT)!
