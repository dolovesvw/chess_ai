#!/usr/bin/env python3
"""
Test script for Eve's StockfishAdapter.

This script tests Eve's Stockfish-based chess AI with different
skill levels, personalities, and features.
"""

import sys
import os
import time
import random
import logging
import chess
from typing import Dict, Any

# Add the project root to the path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../")))

from ai.game_ai.chess_ai.stockfish_adapter import StockfishAdapter

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("stockfish_test")


def print_separator(title: str = None):
    """Print a separator with optional title."""
    print("\n" + "=" * 80)
    if title:
        print(title.center(80))
        print("=" * 80)
    print()


def print_move_info(move_data: Dict[str, Any], skill_level: str = None):
    """Print formatted move information."""
    print(f"{'SKILL LEVEL: ' + skill_level if skill_level else ''}")
    print(f"Move: {move_data['move']}")
    print(f"Commentary: \"{move_data['commentary']}\"")
    
    if move_data.get('opening'):
        print(f"Opening: {move_data['opening']}")
        
    print(f"Confidence: {move_data['confidence']:.2f}")
    print(f"Thinking time: {move_data['thinking_time']:.2f} seconds")
    
    if move_data.get('evaluation'):
        eval_data = move_data['evaluation']
        if eval_data.get('mate'):
            print(f"Evaluation: Mate in {eval_data['mate']}")
        else:
            print(f"Evaluation: {eval_data.get('score', 0)} centipawns")
        print(f"Position assessment: {eval_data.get('description', '')}")


def test_different_skill_levels():
    """Test Eve's play at different skill levels."""
    print_separator("TESTING DIFFERENT SKILL LEVELS")
    
    # Test positions (FEN strings)
    test_position = "r1bqkbnr/pppp1ppp/2n5/4p3/4P3/5N2/PPPP1PPP/RNBQKB1R w KQkq - 2 3"
    
    # Create adapters with different skill levels
    skill_levels = [
        ("Beginner (800 ELO)", 800),
        ("Intermediate (1500 ELO)", 1500),
        ("Expert (2500 ELO)", 2500)
    ]
    
    for skill_name, elo in skill_levels:
        print_separator(f"Testing {skill_name}")
        
        # Create a new adapter with the specified ELO
        adapter = StockfishAdapter(default_rating=elo)
        
        # Get a move from the test position
        move_data = adapter.get_move(test_position)
        
        # Print the move info
        print_move_info(move_data, skill_name)
        
        # Clean up
        adapter.cleanup()
        
        time.sleep(1)  # Pause between tests


def test_personality_traits():
    """Test how different personalities affect move selection."""
    print_separator("TESTING PERSONALITY TRAITS")
    
    # Test position that has multiple reasonable options
    # This is a complex middlegame position with several reasonable moves
    test_position = "r2q1rk1/pp2ppbp/2p2np1/3p4/3P1B2/2N1PN2/PP3PPP/R2QK2R w KQ - 0 10"
    
    personalities = ['aggressive', 'defensive', 'creative', 'solid', 'positional']
    
    for personality in personalities:
        print_separator(f"Testing {personality.capitalize()} Personality")
        
        # Create a new adapter with the specified personality
        adapter = StockfishAdapter(personality=personality, default_rating=1800)
        
        # Get a move from the test position
        move_data = adapter.get_move(test_position)
        
        # Print the move info
        print_move_info(move_data, personality.capitalize())
        
        # Clean up
        adapter.cleanup()
        
        time.sleep(1)  # Pause between tests


def test_opening_book():
    """Test Eve's opening book knowledge."""
    print_separator("TESTING OPENING BOOK KNOWLEDGE")
    
    # Initial position
    initial_position = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
    
    # Create adapter with default settings
    adapter = StockfishAdapter(default_rating=1800)
    
    # Test a few opening sequences
    opening_sequences = [
        # Queen's Gambit
        ("Queen's Gambit", [], "d2d4"),
        ("Queen's Gambit continuation", ["d2d4", "d7d5"], "c2c4"),
        
        # Ruy Lopez
        ("Ruy Lopez", ["e2e4", "e7e5", "g1f3"], "f1b5"),
        
        # King's Gambit
        ("King's Gambit", ["e2e4", "e7e5"], "f2f4"),
    ]
    
    for opening_name, move_history, expected_move in opening_sequences:
        print_separator(f"Testing {opening_name}")
        
        # Set the position with the move history
        adapter.set_position(initial_position, move_history)
        
        # Get the move
        move_data = adapter.get_move()
        
        # Print the move info
        print(f"Expected opening move: {expected_move}")
        print(f"Actual move played: {move_data['move']}")
        print(f"Commentary: \"{move_data['commentary']}\"")
        
        if move_data.get('opening'):
            print(f"Detected opening: {move_data['opening']}")
        
        # Check if the move matches the expected opening move
        if move_data['move'] == expected_move:
            print("\nSUCCESS: Move matches expected opening theory!")
        else:
            print("\nNOTE: Move differs from expected opening (this can happen based on personality)")
            
        time.sleep(1)  # Pause between tests
    
    # Clean up
    adapter.cleanup()


def test_commentary_generation():
    """Test Eve's chess commentary generation."""
    print_separator("TESTING COMMENTARY GENERATION")
    
    # Create adapter with a single personality for consistency
    adapter = StockfishAdapter(personality='creative', default_rating=1800)
    
    # Test positions with interesting features
    test_positions = [
        ("Initial position", "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1", []),
        ("Capture opportunity", "rnbqkbnr/ppp1pppp/8/3p4/4P3/8/PPPP1PPP/RNBQKBNR w KQkq - 0 2", []),
        ("Check opportunity", "rnbqkbnr/pppp1ppp/8/4p3/4P3/5N2/PPPP1PPP/RNBQKB1R w KQkq - 0 3", []),
        ("Complex middlegame", "r1bq1rk1/ppp2ppp/2np1n2/2b1p3/2B1P3/2NP1N2/PPP2PPP/R1BQ1RK1 w - - 0 8", []),
        ("Endgame position", "4k3/8/8/8/8/8/3P4/4K3 w - - 0 1", [])
    ]
    
    for description, fen, moves in test_positions:
        print_separator(f"Commentary for: {description}")
        
        # Get a move
        move_data = adapter.get_move(fen, moves)
        
        # Print commentary
        print(f"Position: {description}")
        print(f"Move: {move_data['move']}")
        print(f"Commentary: \"{move_data['commentary']}\"")
        
        if move_data.get('evaluation'):
            print(f"Position assessment: {move_data['evaluation'].get('description', '')}")
            
        time.sleep(1)  # Pause between tests
    
    # Clean up
    adapter.cleanup()


def test_error_handling():
    """Test error handling in StockfishAdapter."""
    print_separator("TESTING ERROR HANDLING")
    
    # Create adapter
    adapter = StockfishAdapter()
    
    # 1. Test invalid FEN
    print("Testing invalid FEN handling...")
    try:
        invalid_fen = "invalid/fen/string"
        move_data = adapter.get_move(invalid_fen)
        print("Recovered from invalid FEN")
    except Exception as e:
        print(f"Error with invalid FEN: {e}")
    
    # 2. Test invalid moves list
    print("\nTesting invalid moves handling...")
    try:
        invalid_moves = ["e2e4", "invalid_move"]
        move_data = adapter.get_move(None, invalid_moves)
        print("Recovered from invalid moves")
    except Exception as e:
        print(f"Error with invalid moves: {e}")
    
    # 3. Test the error handler directly
    print("\nTesting error handler with fallback...")
    result = adapter.handle_error(Exception("Test error"), "e2e4")
    print(f"Error handler returned: {result}")
    
    # Clean up
    adapter.cleanup()


def test_blunder_generation():
    """Test blunder generation at lower ratings."""
    print_separator("TESTING BLUNDER GENERATION")
    
    # Create a low-rated adapter (more likely to blunder)
    adapter = StockfishAdapter(default_rating=800)
    
    # Simple position where blunders are possible
    test_position = "r1bqkbnr/pppp1ppp/2n5/4p3/3PP3/5N2/PPP2PPP/RNBQKB1R b KQkq - 0 3"
    
    print("Running 5 trials at 800 ELO to look for blunders...")
    for i in range(5):
        print(f"\nTrial {i+1}:")
        
        # Get a move
        move_data = adapter.get_move(test_position)
        
        # Print move info
        print(f"Move: {move_data['move']}")
        print(f"Move type: {move_data.get('move_type', 'unknown')}")
        print(f"Commentary: \"{move_data['commentary']}\"")
        
        # Highlight if it's a blunder
        if move_data.get('move_type') == 'blunder':
            print("THIS IS A BLUNDER!")
            
        time.sleep(0.5)  # Brief pause between trials
    
    # Clean up
    adapter.cleanup()


def test_brilliancy():
    """Test occasional brilliant move generation."""
    print_separator("TESTING BRILLIANCY GENERATION")
    
    # Create adapter with many trials to increase chance of brilliancy
    adapter = StockfishAdapter(default_rating=1500)
    
    # Complex position where brilliancies are possible
    test_position = "r1bq1rk1/ppp2ppp/2np1n2/2b1p3/2B1P3/2NP1N2/PPP2PPP/R1BQ1RK1 w - - 0 8"
    
    print("Running 10 trials looking for brilliancies (5% chance per trial)...")
    found_brilliancy = False
    
    for i in range(10):
        # Get a move
        move_data = adapter.get_move(test_position)
        
        # Check if it's a brilliancy
        if move_data.get('move_type') == 'brilliant':
            print(f"\nBRILLIANCY FOUND on trial {i+1}!")
            print(f"Move: {move_data['move']}")
            print(f"Commentary: \"{move_data['commentary']}\"")
            found_brilliancy = True
            break
            
        print(f"Trial {i+1}: No brilliancy")
        time.sleep(0.5)  # Brief pause between trials
    
    if not found_brilliancy:
        print("\nNo brilliancies found in these trials (this is expected, as they're rare)")
    
    # Clean up
    adapter.cleanup()


def main():
    """Run all tests."""
    try:
        print("\n" + "*" * 80)
        print("*" + " " * 28 + "STOCKFISH ADAPTER TESTS" + " " * 28 + "*")
        print("*" * 80 + "\n")
        
        # Run the individual tests
        test_different_skill_levels()
        test_personality_traits()
        test_opening_book()
        test_commentary_generation()
        test_blunder_generation()
        test_brilliancy()
        test_error_handling()
        
        print("\n" + "*" * 80)
        print("*" + " " * 24 + "ALL STOCKFISH ADAPTER TESTS COMPLETED" + " " * 24 + "*")
        print("*" * 80 + "\n")
        
        return 0
        
    except Exception as e:
        logger.error(f"Test failed with error: {e}", exc_info=True)
        print(f"\nERROR: Test failed with error: {e}")
        print("\n" + "*" * 80)
        print("*" + " " * 32 + "TEST FAILED" + " " * 32 + "*")
        print("*" * 80 + "\n")
        return 1


if __name__ == "__main__":
    sys.exit(main())

