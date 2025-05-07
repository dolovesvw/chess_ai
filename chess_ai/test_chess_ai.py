#!/usr/bin/env python3
"""
Test script for Eve's Chess AI system.

This script demonstrates the functionality of the chess AI by creating a game,
making moves, and observing the AI responses.
"""

import time
import sys
import os
import logging
from typing import Dict, Any

# Add the project root to path to ensure imports work correctly
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../")))

from ai.game_ai.chess_ai.game_controller import ChessGameController


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("chess_ai_test")


def print_separator():
    """Print a separator line for better output readability."""
    print("\n" + "=" * 60 + "\n")


def create_test_game(controller: ChessGameController, user_id: str = "test_user", 
                     platform: str = "test", user_color: str = "white", 
                     difficulty: int = 3) -> str:
    """
    Create a new test game.
    
    Args:
        controller: The chess game controller
        user_id: Test user ID
        platform: Test platform
        user_color: User's color (white or black)
        difficulty: AI difficulty level (1-5)
        
    Returns:
        Session ID of the created game
    """
    print(f"Creating new chess game for user {user_id} on {platform} as {user_color}...")
    print(f"AI difficulty: {difficulty}")
    session_id = controller.create_game(user_id, platform, user_color, difficulty)
    print(f"Game created with session ID: {session_id}")
    return session_id


def make_move_and_print_response(controller: ChessGameController, session_id: str, 
                                move: str) -> Dict[str, Any]:
    """
    Make a chess move and print the response.
    
    Args:
        controller: The chess game controller
        session_id: Game session ID
        move: Move in algebraic notation
        
    Returns:
        Response dictionary from the game controller
    """
    print(f"Making move: {move}")
    response = controller.handle_command(session_id, "move", [move])
    
    if response["success"]:
        print("Move successful!")
        
        # Check if the game is over after our move
        if response.get("game_over", False):
            print(f"Game over: {response['message']}")
            return response
            
        # Display AI response if available
        ai_response = response.get("ai_response", {})
        if ai_response and ai_response.get("success", False):
            print(f"AI responded with move: {ai_response['move']}")
            print(f"AI thinking time: {ai_response['time_taken']:.2f} seconds")
            print(f"AI message: {ai_response.get('message', '')}")
            
            # Check if the game is over after AI move
            if ai_response.get("game_over", False):
                print(f"Game over: {ai_response['message']}")
    else:
        print(f"Move failed: {response.get('error', 'Unknown error')}")
    
    return response


def test_beginner_game():
    """Test a game against the easiest AI level."""
    print_separator()
    print("TESTING BEGINNER LEVEL AI (DIFFICULTY 1)")
    print_separator()
    
    # Create a test directory for game data
    test_data_dir = os.path.join(os.path.dirname(__file__), "test_data", "beginner_test")
    os.makedirs(test_data_dir, exist_ok=True)
    
    # Initialize controller with beginner difficulty
    controller = ChessGameController(data_dir=test_data_dir)
    
    # Create a new game as white against the easiest AI
    session_id = create_test_game(controller, difficulty=1)
    
    # Display initial board
    print("\nInitial board:")
    print(controller.get_board_ascii(session_id))
    print_separator()
    
    # Make a few standard opening moves
    test_moves = ["e2e4", "d2d4", "g1f3"]
    
    for move in test_moves:
        response = make_move_and_print_response(controller, session_id, move)
        
        # Display the updated board
        print("\nCurrent board state:")
        print(controller.get_board_ascii(session_id))
        print_separator()
        
        # If the game ended, stop making moves
        ai_response = response.get("ai_response", {})
        if response.get("game_over", False) or ai_response.get("game_over", False):
            break
            
        # Small delay between moves for better readability
        time.sleep(1)


def test_intermediate_game():
    """Test a game against the intermediate AI level."""
    print_separator()
    print("TESTING INTERMEDIATE LEVEL AI (DIFFICULTY 3)")
    print_separator()
    
    # Create a test directory for game data
    test_data_dir = os.path.join(os.path.dirname(__file__), "test_data", "intermediate_test")
    os.makedirs(test_data_dir, exist_ok=True)
    
    # Initialize controller
    controller = ChessGameController(data_dir=test_data_dir)
    
    # Create a new game as black (AI plays first)
    session_id = create_test_game(controller, user_color="black", difficulty=3)
    
    # Display initial board after AI's first move
    print("\nInitial board (after AI's first move as white):")
    print(controller.get_board_ascii(session_id))
    print_separator()
    
    # User moves as black - standard responses to common white openings
    test_moves = ["e7e5", "b8c6", "g8f6"]
    
    for move in test_moves:
        response = make_move_and_print_response(controller, session_id, move)
        
        # Display the updated board
        print("\nCurrent board state:")
        print(controller.get_board_ascii(session_id))
        print_separator()
        
        # If the game ended, stop making moves
        ai_response = response.get("ai_response", {})
        if response.get("game_over", False) or ai_response.get("game_over", False):
            break
            
        # Small delay between moves for better readability
        time.sleep(1)


def test_error_handling():
    """Test error handling for invalid moves and commands."""
    print_separator()
    print("TESTING ERROR HANDLING")
    print_separator()
    
    # Create a test directory for game data
    test_data_dir = os.path.join(os.path.dirname(__file__), "test_data", "error_test")
    os.makedirs(test_data_dir, exist_ok=True)
    
    # Initialize controller
    controller = ChessGameController(data_dir=test_data_dir)
    
    # Create a new game
    session_id = create_test_game(controller)
    
    # Display initial board
    print("\nInitial board:")
    print(controller.get_board_ascii(session_id))
    print_separator()
    
    # Test 1: Invalid notation format
    print("\nTesting invalid notation format: 'e2-e4'")
    response = make_move_and_print_response(controller, session_id, "e2-e4")
    print_separator()
    
    # Test 2: Out of bounds coordinates
    print("\nTesting out of bounds coordinates: 'j9j8'")
    response = make_move_and_print_response(controller, session_id, "j9j8")
    print_separator()
    
    # Test 3: Moving a piece that isn't there
    print("\nTesting moving a piece that isn't there: 'e5e6'")
    response = make_move_and_print_response(controller, session_id, "e5e6")
    print_separator()
    
    # Test 4: Invalid move (trying to move opponent's piece)
    print("\nTesting trying to move opponent's piece: 'e7e5'")
    response = make_move_and_print_response(controller, session_id, "e7e5")
    print_separator()
    
    # Make a valid move to show the contrast
    print("\nMaking a valid move: 'e2e4'")
    response = make_move_and_print_response(controller, session_id, "e2e4")
    print("\nCurrent board state:")
    print(controller.get_board_ascii(session_id))
    print_separator()


def test_game_commands():
    """Test various game commands like resign, status, and board display."""
    print_separator()
    print("TESTING GAME COMMANDS")
    print_separator()
    
    # Create a test directory for game data
    test_data_dir = os.path.join(os.path.dirname(__file__), "test_data", "commands_test")
    os.makedirs(test_data_dir, exist_ok=True)
    
    # Initialize controller
    controller = ChessGameController(data_dir=test_data_dir)
    
    # Create a new game
    session_id = create_test_game(controller)
    
    # Make a move to advance the game state
    print("\nMaking a valid move: 'e2e4'")
    response = make_move_and_print_response(controller, session_id, "e2e4")
    
    # Test status command
    print("\nTesting status command:")
    status = controller.handle_command(session_id, "status")
    print(f"Active color: {status.get('active_color')}")
    print(f"Moves played: {status.get('moves_played')}")
    print(f"Check: {status.get('is_check')}")
    print(f"Checkmate: {status.get('is_checkmate')}")
    print(f"Stalemate: {status.get('is_stalemate')}")
    print_separator()
    
    # Test get_game_state method
    print("\nTesting get_game_state method:")
    game_state = controller.get_game_state(session_id, include_history=True)
    print(f"Session ID: {game_state.get('session_id')}")
    print(f"User color: {game_state.get('user_color')}")
    print(f"Is user's turn: {game_state.get('is_user_turn')}")
    print(f"FEN: {game_state.get('fen')}")
    print(f"Move history length: {len(game_state.get('move_history', []))}")
    print_separator()
    
    # Test resignation
    print("\nTesting resignation:")
    resign_response = controller.handle_command(session_id, "resign")
    print(f"Resignation successful: {resign_response.get('success')}")
    print(f"Game outcome: {resign_response.get('outcome')}")
    print(f"Reason: {resign_response.get('reason')}")
    print_separator()
    
    # Verify game is over after resignation
    status = controller.handle_command(session_id, "status")
    print(f"Game over: {status.get('game_over')}")
    print(f"Final outcome: {status.get('outcome')}")


def main():
    """Main test function."""
    try:
        print("\n" + "*" * 80)
        print("*" + " " * 28 + "CHESS AI SYSTEM TEST" + " " * 28 + "*")
        print("*" * 80 + "\n")
        
        # Run individual test modules
        test_beginner_game()
        test_intermediate_game()
        test_error_handling()
        test_game_commands()
        
        print("\n" + "*" * 80)
        print("*" + " " * 24 + "ALL TESTS COMPLETED SUCCESSFULLY" + " " * 24 + "*")
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

