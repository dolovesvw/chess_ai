#!/usr/bin/env python3
"""
Eve Chess AI Demonstration

This script demonstrates Eve's chess-playing capabilities with different
skill levels, personalities, and features.
"""

import os
import sys
import time
import random
import chess
import logging
from typing import Dict, Any, List

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../")))

from ai.game_ai.chess_ai.stockfish_adapter import StockfishAdapter

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("eve_chess_demo")


class ChessDemonstration:
    """Chess demonstration for Eve's AI capabilities."""
    
    def __init__(self):
        """Initialize the demonstration."""
        self.demos_run = set()
        self.current_adapter = None
    
    def print_header(self, title: str):
        """Print a formatted header."""
        print("\n" + "=" * 80)
        print(f"★  {title}  ★".center(80))
        print("=" * 80 + "\n")
    
    def print_move_details(self, move_data: Dict[str, Any], turn_number: int, player: str = "Eve"):
        """Print details about a chess move."""
        print(f"\n━━━━ {player}'s Move {turn_number} ━━━━")
        print(f"Move: {move_data['move']}")
        print(f"Commentary: \"{move_data['commentary']}\"")
        
        if move_data.get('opening'):
            print(f"Opening: {move_data['opening']}")
        
        if move_data.get('evaluation'):
            eval_data = move_data['evaluation']
            print(f"Position assessment: {eval_data.get('description', '')}")
        
        print(f"Thinking time: {move_data['thinking_time']:.2f} seconds")
    
    def print_chess_board(self, board: chess.Board):
        """Print ASCII representation of the chess board."""
        print("\nCurrent Board Position:")
        print("    a b c d e f g h")
        print("  +-----------------+")
        
        for rank in range(7, -1, -1):
            print(f"{rank+1} | ", end="")
            for file in range(8):
                square = chess.square(file, rank)
                piece = board.piece_at(square)
                if piece:
                    symbol = piece.symbol()
                else:
                    symbol = "."
                print(f"{symbol} ", end="")
            print(f"| {rank+1}")
            
        print("  +-----------------+")
        print("    a b c d e f g h\n")
    
    def simulate_opponent_move(self, board: chess.Board, skill_level: int = 10):
        """Simulate an opponent's move at a given skill level."""
        # Create a temporary Stockfish adapter for the opponent
        opponent = StockfishAdapter(default_rating=1500)
        opponent.stockfish.set_skill_level(skill_level)
        opponent.stockfish.set_depth(5)  # Lower depth for faster responses
        
        # Get the opponent's move
        fen = board.fen()
        move_data = opponent.get_move(fen)
        
        # Apply the move to the board
        board.push_uci(move_data['move'])
        
        # Clean up
        opponent.cleanup()
        
        return move_data
    
    def demo_skill_levels(self):
        """Demonstrate Eve playing at different skill levels."""
        self.print_header("Eve Playing at Different Skill Levels")
        
        skill_levels = [
            ("Beginner (800 ELO)", 800),
            ("Intermediate (1500 ELO)", 1500),
            ("Expert (2500 ELO)", 2500)
        ]
        
        for skill_name, elo in skill_levels:
            print(f"\n▶ {skill_name} ◀")
            print("-" * 50)
            
            # Create adapter with this skill level
            adapter = StockfishAdapter(default_rating=elo)
            self.current_adapter = adapter
            
            # Start from the initial position
            board = chess.Board()
            
            # Make a few moves
            for i in range(3):
                # Simulate opponent move first (if not the first move)
                if i > 0 or board.turn == chess.BLACK:
                    opponent_move = self.simulate_opponent_move(board)
                    print(f"\nOpponent plays: {opponent_move['move']}")
                    self.print_chess_board(board)
                
                # Eve's turn
                if board.is_game_over():
                    print("Game over!")
                    break
                    
                move_data = adapter.get_move(board.fen())
                
                # Apply Eve's move
                board.push_uci(move_data['move'])
                
                # Print move details
                self.print_move_details(move_data, i+1)
                self.print_chess_board(board)
                
                time.sleep(1)  # Short pause between moves
            
            # Cleanup
            adapter.cleanup()
            
            if skill_name != skill_levels[-1][0]:
                input("\nPress Enter to continue to the next skill level...")
    
    def demo_personalities(self):
        """Demonstrate Eve's different chess personalities."""
        self.print_header("Eve's Different Chess Personalities")
        
        personalities = [
            "aggressive", "defensive", "creative", "solid", "positional"
        ]
        
        # Use the same position for all personalities to see the differences
        custom_fen = "r1bqkbnr/pppp1ppp/2n5/4p3/4P3/5N2/PPPP1PPP/RNBQKB1R w KQkq - 2 3"
        
        for personality in personalities:
            print(f"\n▶ {personality.capitalize()} Personality ◀")
            print("-" * 50)
            
            # Create adapter with this personality
            adapter = StockfishAdapter(personality=personality, default_rating=1800)
            self.current_adapter = adapter
            
            # Set up the position
            board = chess.Board(custom_fen)
            self.print_chess_board(board)
            
            # Let Eve make a move with this personality
            move_data = adapter.get_move(board.fen())
            
            # Apply the move
            board.push_uci(move_data['move'])
            
            # Print move details
            self.print_move_details(move_data, 1)
            self.print_chess_board(board)
            
            # Cleanup
            adapter.cleanup()
            
            if personality != personalities[-1]:
                input("\nPress Enter to continue to the next personality...")
    
    def demo_opening_book(self):
        """Demonstrate Eve's opening book knowledge."""
        self.print_header("Eve's Opening Book Knowledge")
        
        # Create adapter
        adapter = StockfishAdapter(default_rating=1800)
        self.current_adapter = adapter
        
        # Test a few opening sequences
        opening_sequences = [
            ("Queen's Gambit", []),
            ("Sicilian Defense", ["e2e4"]),
            ("French Defense", ["e2e4", "e7e6"]),
            ("Ruy Lopez", ["e2e4", "e7e5", "g1f3"])
        ]
        
        for opening_name, moves in opening_sequences:
            print(f"\n▶ Testing: {opening_name} ◀")
            print("-" * 50)
            
            # Set up the board with the moves
            board = chess.Board()
            for move in moves:
                board.push_uci(move)
            
            self.print_chess_board(board)
            
            # Get Eve's move
            adapter.set_position(board.fen(), moves)
            move_data = adapter.get_move()
            
            # Apply the move
            board.push_uci(move_data['move'])
            
            # Print move details
            self.print_move_details(move_data, len(moves) + 1)
            self.print_chess_board(board)
            
            if opening_name != opening_sequences[-1][0]:
                input("\nPress Enter to continue to the next opening...")
        
        # Cleanup
        adapter.cleanup()
    
    def demo_blunders_and_brilliancies(self):
        """Demonstrate Eve's occasional blunders and brilliancies."""
        self.print_header("Eve's Blunders and Brilliancies")
        
        # First: Blunders at low rating
        print("\n▶ Potential Blunders (800 ELO) ◀")
        print("-" * 50)
        
        # Create a low-rated adapter (more likely to blunder)
        adapter = StockfishAdapter(default_rating=800)
        self.current_adapter = adapter
        
        # Position where blunders are possible
        blunder_fen = "r1bqkbnr/pppp1ppp/2n5/4p3/3PP3/5N2/PPP2PPP/RNBQKB1R b KQkq - 0 3"
        board = chess.Board(blunder_fen)
        
        self.print_chess_board(board)
        print("This position has obvious best moves. Let's see if beginner Eve blunders...")
        
        # Try 3 times to get a blunder
        for i in range(3):
            move_data = adapter.get_move(board.fen())
            board_copy = chess.Board(blunder_fen)
            board_copy.push_uci(move_data['move'])
            
            # Print move details
            self.print_move_details(move_data, i+1)
            
            # Check if it's a "blunder"
            if move_data.get('move_type') == 'blunder':
                print("⚠️ THIS MOVE IS A BLUNDER! ⚠️")
            
            time.sleep(1)
        
        adapter.cleanup()
        
        # Second: Brilliancies at higher rating
        print("\n\n▶ Potential Brilliancies (1800 ELO) ◀")
        print("-" * 50)
        
        # Create an adapter that might find brilliancies
        adapter = StockfishAdapter(default_rating=1800, personality='creative')
        self.current_adapter = adapter
        
        # Position where tactical brilliancies are possible
        brilliancy_fen = "r1bq1rk1/ppp2ppp/2np1n2/2b1p3/2B1P3/2NP1N2/PPP2PPP/R1BQ1RK1 w - - 0 8"
        board = chess.Board(brilliancy_fen)
        
        self.print_chess_board(board)
        print("This position has tactical opportunities. Let's see if Eve finds a brilliancy...")
        
        # Try 5 times with different positions to get a brilliancy
        found_brilliancy = False
        for i in range(5):
            # Slightly modify the position each time
            if i > 0:
                # Apply a random legal move to change the position
                legal_moves = list(board.legal_moves)
                if legal_moves:
                    board.push(random.choice(legal_moves))
                    self.print_chess_board(board)
            
            move_data = adapter.get_move(board.fen())
            
            # Print move details
            self.print_move_details(move_data, i+1)
            
            # Check if it's a "brilliancy"
            if move_data.get('move_type') == 'brilliant':
                print("✨ BRILLIANCY FOUND! ✨")
                found_brilliancy = True
                break
            
            time.sleep(1)
        
        if not found_brilliancy:
            print("\nNo brilliancies found in these positions (they're quite rare).")
        
        adapter.cleanup()
    
    def demo_commentary(self):
        """Demonstrate Eve's chess commentary for different position types."""
        self.print_header("Eve's Chess Commentary")
        
        # Create adapter
        adapter = StockfishAdapter(default_rating=1800)
        self.current_adapter = adapter
        
        # Test positions with interesting features
        test_positions = [
            ("Initial position", "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1", []),
            ("Capture opportunity", "rnbqkbnr/ppp1pppp/8/3p4/4P3/8/PPPP1PPP/RNBQKBNR w KQkq - 0 2", []),
            ("Check opportunity", "rnbqkbnr/pppp1ppp/8/4p3/4P3/5N2/PPPP1PPP/RNBQKB1R w KQkq - 0 3", []),
            ("Complex middlegame", "r1bq1rk1/ppp2ppp/2np1n2/2b1p3/2B1P3/2NP1N2/PPP2PPP/R1BQ1RK1 w - - 0 8", []),
            ("Winning position", "r4rk1/ppp2ppp/2n5/8/3Pp3/P1P1P3/2P3PP/R1B1KB1R w KQ - 0 13", []),
            ("Losing position", "r1bqkb1r/pppp1ppp/2n2n2/4p3/3PP3/2N5/PPP2PPP/R1BQKBNR b KQkq - 0 4", [])
        ]
        
        for description, fen, moves in test_positions:
            print(f"\n▶ {description} ◀")
            print("-" * 50)
            
            # Set up the board
            board = chess.Board(fen)
            for move in moves:
                board.push_uci(move)
                
            self.print_chess_board(board)
            
            # Get Eve's move
            move_data = adapter.get_move(board.fen())
            
            # Print move details
            self.print_move_details(move_data, 1)
            
            if description != test_positions[-1][0]:
                input("\nPress Enter to continue to the next position...")
        
        # Cleanup
        adapter.cleanup()
    
    def run_demo(self, demo_name: str = None):
        """Run a specific demo or all demos."""
        demos = {
            "skill": self.demo_skill_levels,
            "personality": self.demo_personalities,
            "opening": self.demo_opening_book,
            "blunder": self.demo_blunders_and_brilliancies,
            "commentary": self.demo_commentary,
            "all": None  # Special case to run all demos
        }
        
        if demo_name is None:
            # Show menu if no demo specified
            self.show_menu()
            return
            
        if demo_name not in demos:
            print(f"Unknown demo: {demo_name}")
            print(f"Available demos: {', '.join(demos.keys())}")
            return
            
        if demo_name == "all":
            print("\n🎮 Running all demos sequentially 🎮\n")
            for name, demo_fn in demos.items():
                if name != "all" and name not in self.demos_run:
                    try:
                        print(f"\nRunning demo: {name}")
                        demo_fn()
                        self.demos_run.add(name)
                        input("\nPress Enter to continue to the next demo...")
                    except Exception as e:
                        print(f"Error running demo {name}: {e}")
            print("\n🎮 All demos completed! 🎮")
        else:
            # Run the specified demo
            demo_fn = demos[demo_name]
            try:
                demo_fn()
                self.demos_run.add(demo_name)
            except Exception as e:
                print(f"Error running demo {demo_name}: {e}")
    
    def show_menu(self):
        """Show interactive demo selection menu."""
        while True:
            self.print_header("Eve's Chess AI Demonstration Menu")
            
            print("Select a demo to run:\n")
            print("1. Skill Levels - Eve at different ELO ratings (800, 1500, 2500)")
            print("2. Personalities - Eve's different chess personalities")
            print("3. Opening Book - Eve's opening theory knowledge")
            print("4. Blunders & Brilliancies - Mistakes and exceptional moves")
            print("5. Commentary - Eve's move commentary in different positions")
            print("6. Run All Demos - Run all demos sequentially")
            print("0. Exit\n")
            
            choice = input("Enter your choice (0-6): ").strip()
            
            demo_map = {
                "1": "skill",
                "2": "personality",
                "3": "opening",
                "4": "blunder",
                "5": "commentary",
                "6": "all"
            }
            
            if choice == "0":
                print("\nExiting Eve's Chess AI Demonstration. Goodbye!")
                break
                
            if choice in demo_map:
                try:
                    self.run_demo(demo_map[choice])
                except KeyboardInterrupt:
                    print("\n\nDemo interrupted. Returning to menu...")
                except Exception as e:
                    print(f"\nError running demo: {e}")
                    print("Returning to menu...")
            else:
                print("\nInvalid choice. Please enter a number between 0 and 6.")
            
            # Clean up any lingering adapters
            if self.current_adapter is not None:
                try:
                    self.current_adapter.cleanup()
                except:
                    pass
                self.current_adapter = None


def main():
    """Main function to run the demo."""
    print("\n" + "*" * 80)
    print("*" + " " * 26 + "EVE'S CHESS AI DEMONSTRATION" + " " * 27 + "*")
    print("*" * 80 + "\n")
    
    print("This demonstration shows Eve's chess capabilities with different skill levels,")
    print("personalities, and features. Eve can play at varying ELO ratings, demonstrate")
    print("different playing styles, and occasionally make blunders or find brilliant moves.")
    print("\nEach demo will show how Eve calculates moves and generates commentary")
    print("that matches her personality and the game situation.")
    
    demo = ChessDemonstration()
    
    # Check if a specific demo was requested from command line
    if len(sys.argv) > 1:
        demo_name = sys.argv[1].lower()
        demo.run_demo(demo_name)
    else:
        # Show interactive menu
        try:
            demo.show_menu()
        except KeyboardInterrupt:
            print("\n\nDemo interrupted. Exiting...")
        except Exception as e:
            print(f"\nError: {e}")
            print("Exiting...")
    
    print("\nThank you for exploring Eve's chess capabilities!")


if __name__ == "__main__":
    main()

