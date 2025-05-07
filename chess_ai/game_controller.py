"""
Chess game controller module.

This module handles chess game sessions, commands, and interactions,
serving as the interface between the AI and various platforms.
"""

import json
import logging
import time
import os
import uuid
import datetime
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any, Union

from .state_manager import ChessState, PieceType, PieceColor
from .ai_engine import ChessAI


# Configure logging
logger = logging.getLogger(__name__)


class GameSession:
    """
    Represents a single chess game session between a user and Eve.
    
    This class encapsulates all the data for a specific game, including
    the game state, player information, and session metadata.
    """
    
    def __init__(self, 
                 session_id: str, 
                 user_id: str, 
                 platform: str, 
                 user_color: PieceColor = PieceColor.WHITE,
                 difficulty: int = 3):
        """
        Initialize a new game session.
        
        Args:
            session_id: Unique identifier for this game session
            user_id: Identifier for the user (platform-specific)
            platform: Platform identifier (discord, twitch, etc.)
            user_color: Color the user is playing (WHITE or BLACK)
            difficulty: AI difficulty level (1-5)
        """
        self.session_id = session_id
        self.user_id = user_id
        self.platform = platform
        self.user_color = user_color
        self.difficulty = difficulty
        
        # Game state
        self.state = ChessState()
        
        # Session metadata
        self.created_at = datetime.datetime.now().isoformat()
        self.last_activity = self.created_at
        self.moves_played = 0
        self.is_active = True
        self.outcome = None  # None, "white_win", "black_win", "draw"
        self.outcome_reason = None  # None, "checkmate", "resignation", "stalemate", etc.
        
        # Game history for analysis and display
        self.move_history: List[Dict[str, Any]] = []
        
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the session to a dictionary for serialization.
        
        Returns:
            Dictionary representation of the session
        """
        return {
            "session_id": self.session_id,
            "user_id": self.user_id,
            "platform": self.platform,
            "user_color": self.user_color.value,
            "difficulty": self.difficulty,
            "created_at": self.created_at,
            "last_activity": self.last_activity,
            "moves_played": self.moves_played,
            "is_active": self.is_active,
            "outcome": self.outcome,
            "outcome_reason": self.outcome_reason,
            "state_fen": self.state.get_fen(),
            "move_history": self.move_history
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'GameSession':
        """
        Create a session from a dictionary representation.
        
        Args:
            data: Dictionary representation of a session
            
        Returns:
            New GameSession instance
        """
        # Create a new session with basic parameters
        session = cls(
            session_id=data["session_id"],
            user_id=data["user_id"],
            platform=data["platform"],
            user_color=PieceColor.WHITE if data["user_color"] == "w" else PieceColor.BLACK,
            difficulty=data["difficulty"]
        )
        
        # Restore metadata
        session.created_at = data["created_at"]
        session.last_activity = data["last_activity"]
        session.moves_played = data["moves_played"]
        session.is_active = data["is_active"]
        session.outcome = data["outcome"]
        session.outcome_reason = data["outcome_reason"]
        
        # Restore game state from FEN
        session.state.set_from_fen(data["state_fen"])
        
        # Restore move history
        session.move_history = data["move_history"]
        
        return session
    
    def update_activity(self) -> None:
        """Update the last activity timestamp for this session."""
        self.last_activity = datetime.datetime.now().isoformat()
    
    def record_move(self, move_from: Tuple[int, int], move_to: Tuple[int, int], 
                   algebraic: str, move_time: float, evaluation: int) -> None:
        """
        Record a move in the session history.
        
        Args:
            move_from: Starting coordinates (x, y)
            move_to: Target coordinates (x, y)
            algebraic: Move in algebraic notation
            move_time: Time taken to make the move (seconds)
            evaluation: Position evaluation after the move
        """
        self.moves_played += 1
        self.update_activity()
        
        move_data = {
            "move_number": self.moves_played,
            "player": "user" if self.state.active_color == self.user_color else "ai",
            "from": move_from,
            "to": move_to,
            "algebraic": algebraic,
            "time": move_time,
            "evaluation": evaluation,
            "timestamp": datetime.datetime.now().isoformat()
        }
        
        self.move_history.append(move_data)
    
    def end_game(self, outcome: str, reason: str) -> None:
        """
        End the game with the specified outcome.
        
        Args:
            outcome: Game outcome ("white_win", "black_win", "draw")
            reason: Reason for the outcome ("checkmate", "resignation", etc.)
        """
        self.is_active = False
        self.outcome = outcome
        self.outcome_reason = reason
        self.update_activity()


class ChessGameController:
    """
    Controller for chess games played with Eve.
    
    This class manages multiple chess games across different platforms,
    handles user commands, and coordinates between the UI and game logic.
    """
    
    def __init__(self, data_dir: str = None):
        """
        Initialize the chess game controller.
        
        Args:
            data_dir: Directory to store game data (default: ./data/chess_games)
        """
        # Set up data directory
        if data_dir is None:
            self.data_dir = os.path.join("data", "chess_games")
        else:
            self.data_dir = data_dir
            
        # Create data directory if it doesn't exist
        os.makedirs(self.data_dir, exist_ok=True)
        
        # Initialize AI engine
        self.ai = ChessAI()
        
        # Active games dictionary: {session_id: GameSession}
        self.active_games: Dict[str, GameSession] = {}
        
        # Load any active games from disk
        self._load_active_games()
        
        logger.info(f"Chess game controller initialized with {len(self.active_games)} active games")
    
    def _load_active_games(self) -> None:
        """Load active game sessions from disk."""
        session_files = Path(self.data_dir).glob("active_*.json")
        
        for file_path in session_files:
            try:
                with open(file_path, 'r') as f:
                    session_data = json.load(f)
                    
                session = GameSession.from_dict(session_data)
                self.active_games[session.session_id] = session
                logger.info(f"Loaded active game session {session.session_id}")
            except Exception as e:
                logger.error(f"Error loading game session from {file_path}: {e}")
    
    def _save_game_session(self, session: GameSession) -> None:
        """
        Save a game session to disk.
        
        Args:
            session: Game session to save
        """
        # Determine filename based on session status
        prefix = "active" if session.is_active else "completed"
        filename = f"{prefix}_{session.session_id}.json"
        file_path = os.path.join(self.data_dir, filename)
        
        # Save session data
        try:
            with open(file_path, 'w') as f:
                json.dump(session.to_dict(), f, indent=2)
                
            logger.info(f"Saved game session {session.session_id} to {file_path}")
        except Exception as e:
            logger.error(f"Error saving game session {session.session_id}: {e}")
    
    def create_game(self, user_id: str, platform: str, 
                   user_color: str = "white", difficulty: int = 3) -> str:
        """
        Create a new chess game session.
        
        Args:
            user_id: User identifier (platform-specific)
            platform: Platform identifier (discord, twitch, etc.)
            user_color: Color for the user to play ("white" or "black")
            difficulty: AI difficulty level (1-5)
            
        Returns:
            Session ID for the new game
        """
        # Validate parameters
        if user_color.lower() not in ["white", "black"]:
            user_color = "white"
            
        if not (1 <= difficulty <= 5):
            difficulty = 3
            
        # Convert user_color to PieceColor enum
        piece_color = PieceColor.WHITE if user_color.lower() == "white" else PieceColor.BLACK
        
        # Generate a unique session ID
        session_id = str(uuid.uuid4())
        
        # Create the game session
        session = GameSession(
            session_id=session_id,
            user_id=user_id,
            platform=platform,
            user_color=piece_color,
            difficulty=difficulty
        )
        
        # Store the session
        self.active_games[session_id] = session
        
        # Save to disk
        self._save_game_session(session)
        
        # If AI plays first (user is black), make AI move
        if piece_color == PieceColor.BLACK:
            self.make_ai_move(session_id)
        
        logger.info(f"Created new game session {session_id} for user {user_id} on {platform}")
        return session_id
    
    def get_game(self, session_id: str) -> Optional[GameSession]:
        """
        Get a game session by ID.
        
        Args:
            session_id: Game session ID
            
        Returns:
            The game session, or None if not found
        """
        return self.active_games.get(session_id)
    
    def get_user_games(self, user_id: str, platform: str) -> List[GameSession]:
        """
        Get all active games for a specific user.
        
        Args:
            user_id: User identifier
            platform: Platform identifier
            
        Returns:
            List of active game sessions for the user
        """
        return [
            session for session in self.active_games.values()
            if session.user_id == user_id and session.platform == platform and session.is_active
        ]
    
    def handle_command(self, session_id: str, command: str, args: List[str] = None) -> Dict[str, Any]:
        """
        Handle a chess game command.
        
        Args:
            session_id: Game session ID
            command: Command string (move, resign, draw, etc.)
            args: Command arguments
            
        Returns:
            Response dictionary with command result
        """
        if args is None:
            args = []
            
        # Get the game session
        session = self.get_game(session_id)
        if session is None:
            return {"success": False, "error": "Game session not found"}
        
        # Handle different commands
        command = command.lower()
        
        if command == "move":
            if len(args) < 1:
                return {"success": False, "error": "Move command requires algebraic notation (e.g., 'e2e4')"}
                
            return self.make_move(session_id, args[0])
            
        elif command == "resign":
            return self.resign_game(session_id)
            
        elif command == "draw":
            # For simplicity, AI always accepts draw offers
            winner = "black" if session.user_color == PieceColor.WHITE else "white"
            loser = "white" if winner == "black" else "black"
            
            session.end_game(
                f"{winner}_win", 
                f"{loser}_resignation"
            )
            self._save_game_session(session)
            
            return {
                "success": True,
                "message": "Draw offer accepted",
                "game_over": True,
                "outcome": "draw",
                "reason": "agreement"
            }
            
        elif command == "status":
            # Return game status information
            is_check = session.state.is_check()
            is_checkmate = session.state.is_checkmate()
            is_stalemate = session.state.is_stalemate()
            
            return {
                "success": True,
                "active_color": "white" if session.state.active_color == PieceColor.WHITE else "black",
                "user_color": "white" if session.user_color == PieceColor.WHITE else "black",
                "moves_played": session.moves_played,
                "is_check": is_check,
                "is_checkmate": is_checkmate,
                "is_stalemate": is_stalemate,
                "game_over": not session.is_active,
                "outcome": session.outcome,
                "reason": session.outcome_reason
            }
            
        else:
            return {"success": False, "error": f"Unknown command: {command}"}
    
    def make_move(self, session_id: str, algebraic_move: str) -> Dict[str, Any]:
        """
        Make a user move in algebraic notation.
        
        Args:
            session_id: Game session ID
            algebraic_move: Move in algebraic notation (e.g., "e2e4")
            
        Returns:
            Response dictionary with move result
        """
        # Get the game session
        session = self.get_game(session_id)
        if session is None:
            return {"success": False, "error": "Game session not found"}
            
        # Check if game is still active
        if not session.is_active:
            return {"success": False, "error": "Game is already over"}
            
        # Check if it's the user's turn
        if session.state.active_color != session.user_color:
            return {"success": False, "error": "It's not your turn"}
            
        try:
            # Convert algebraic notation to coordinates
            from_x, from_y, to_x, to_y = session.state.algebraic_to_coords(algebraic_move)
            
            # Record start time for performance tracking
            start_time = time.time()
            
            # Make the move on the game state
            move_successful = session.state.make_move(from_x, from_y, to_x, to_y)
            
            if not move_successful:
                return {"success": False, "error": "Invalid move"}
                
            # Calculate move time
            move_time = time.time() - start_time
            
            # Record the move in session history
            # For evaluation, we'd normally use a proper evaluation, but here we'll use 0 as placeholder
            evaluation = 0
            session.record_move(
                (from_x, from_y), 
                (to_x, to_y), 
                algebraic_move, 
                move_time,
                evaluation
            )
            
            # Check for game end conditions
            if session.state.is_checkmate():
                # Game over - user wins by checkmate
                winner_color = "white" if session.user_color == PieceColor.WHITE else "black"
                session.end_game(f"{winner_color}_win", "checkmate")
                self._save_game_session(session)
                
                return {
                    "success": True,
                    "message": f"Checkmate! You win!",
                    "move": algebraic_move,
                    "game_over": True,
                    "outcome": f"{winner_color}_win",
                    "reason": "checkmate"
                }
                
            if session.state.is_stalemate():
                # Game over - draw by stalemate
                session.end_game("draw", "stalemate")
                self._save_game_session(session)
                
                return {
                    "success": True,
                    "message": "Stalemate! The game is a draw.",
                    "move": algebraic_move,
                    "game_over": True,
                    "outcome": "draw",
                    "reason": "stalemate"
                }
                
            # Save the updated game state
            self._save_game_session(session)
            
            # If game continues, make AI move
            ai_response = self.make_ai_move(session_id)
            
            # Return combined response with both the user's move and AI's response
            response = {
                "success": True,
                "message": "Move successful",
                "move": algebraic_move,
                "ai_response": ai_response
            }
            
            return response
            
        except ValueError as e:
            # Handle format errors in algebraic notation
            return {"success": False, "error": str(e)}
        except Exception as e:
            logger.error(f"Error making move in session {session_id}: {e}")
            return {"success": False, "error": "An unexpected error occurred"}
    
    def make_ai_move(self, session_id: str) -> Dict[str, Any]:
        """
        Generate and execute an AI move for the given game.
        
        Args:
            session_id: Game session ID
            
        Returns:
            Response dictionary with AI move information
        """
        # Get the game session
        session = self.get_game(session_id)
        if session is None:
            return {"success": False, "error": "Game session not found"}
            
        # Check if game is still active
        if not session.is_active:
            return {"success": False, "error": "Game is already over"}
            
        # Check if it's the AI's turn
        if session.state.active_color == session.user_color:
            return {"success": False, "error": "It's not AI's turn"}
        
        # Set AI difficulty for this game
        self.ai.set_difficulty(session.difficulty)
        
        # Measure time for AI thinking
        start_time = time.time()
        
        try:
            # Get the best move from the AI
            best_move = self.ai.get_best_move(session.state)
            
            if best_move is None:
                # No legal moves available - this shouldn't happen unless the game is already over
                if session.state.is_checkmate():
                    winner_color = "white" if session.user_color == PieceColor.WHITE else "black"
                    session.end_game(f"{winner_color}_win", "checkmate")
                elif session.state.is_stalemate():
                    session.end_game("draw", "stalemate")
                else:
                    # Some other reason
                    session.end_game("draw", "no_legal_moves")
                self._save_game_session(session)
                
                return {
                    "success": False,
                    "error": "No legal moves available",
                    "game_over": True,
                    "outcome": session.outcome,
                    "reason": session.outcome_reason
                }
                
            # Unpack the move coordinates
            (from_x, from_y), (to_x, to_y) = best_move
            
            # Apply the move to the state
            move_successful = session.state.make_move(from_x, from_y, to_x, to_y)
            
            if not move_successful:
                return {"success": False, "error": "AI generated an invalid move"}
                
            # Calculate total move time
            move_time = time.time() - start_time
            
            # Convert to algebraic notation for user display
            algebraic_move = session.state.coords_to_algebraic(from_x, from_y, to_x, to_y)
            
            # Get evaluation of position after move
            evaluation = self.ai.evaluator.evaluate(session.state)
            
            # Record the AI move
            session.record_move(
                (from_x, from_y),
                (to_x, to_y),
                algebraic_move,
                move_time,
                evaluation
            )
            
            # Check for game end conditions
            is_checkmate = session.state.is_checkmate()
            is_stalemate = session.state.is_stalemate()
            is_check = session.state.is_check()
            
            response = {
                "success": True,
                "move": algebraic_move,
                "from": (from_x, from_y),
                "to": (to_x, to_y),
                "time_taken": move_time,
                "evaluation": evaluation,
                "nodes_searched": self.ai.get_statistics()["nodes_searched"],
                "is_check": is_check,
                "game_over": False
            }
            
            if is_checkmate:
                # Game over - AI wins by checkmate
                winner_color = "black" if session.user_color == PieceColor.WHITE else "white"
                session.end_game(f"{winner_color}_win", "checkmate")
                response["game_over"] = True
                response["outcome"] = f"{winner_color}_win"
                response["reason"] = "checkmate"
                response["message"] = "Checkmate! Eve wins!"
            elif is_stalemate:
                # Game over - draw by stalemate
                session.end_game("draw", "stalemate")
                response["game_over"] = True
                response["outcome"] = "draw"
                response["reason"] = "stalemate"
                response["message"] = "Stalemate! The game is a draw."
            elif is_check:
                response["message"] = "Check!"
            else:
                response["message"] = "Eve has moved."
                
            # Save the updated game state
            self._save_game_session(session)
            
            return response
            
        except Exception as e:
            logger.error(f"Error making AI move in session {session_id}: {e}")
            return {"success": False, "error": "An unexpected error occurred with the AI move"}
    
    def resign_game(self, session_id: str) -> Dict[str, Any]:
        """
        Handle player resignation from a game.
        
        Args:
            session_id: Game session ID
            
        Returns:
            Response dictionary with resignation result
        """
        # Get the game session
        session = self.get_game(session_id)
        if session is None:
            return {"success": False, "error": "Game session not found"}
            
        # Check if game is still active
        if not session.is_active:
            return {"success": False, "error": "Game is already over"}
            
        # Determine winner based on user color (opposite of user color wins)
        winner_color = "black" if session.user_color == PieceColor.WHITE else "white"
        loser_color = "white" if winner_color == "black" else "black"
        
        # End the game
        session.end_game(f"{winner_color}_win", f"{loser_color}_resignation")
        
        # Save the updated session
        self._save_game_session(session)
        
        return {
            "success": True,
            "message": "You have resigned the game.",
            "game_over": True,
            "outcome": f"{winner_color}_win",
            "reason": f"{loser_color}_resignation"
        }
    
    def cleanup_inactive_games(self, max_age_days: int = 30) -> int:
        """
        Archive or remove inactive game sessions older than specified age.
        
        Args:
            max_age_days: Maximum age in days for inactive games
            
        Returns:
            Number of sessions cleaned up
        """
        # Calculate cutoff date
        cutoff_time = (datetime.datetime.now() - 
                        datetime.timedelta(days=max_age_days)).isoformat()
        
        sessions_to_remove = []
        
        # Find inactive sessions older than cutoff
        for session_id, session in self.active_games.items():
            if not session.is_active and session.last_activity < cutoff_time:
                sessions_to_remove.append(session_id)
                
                # If session is already saved as completed, archive it
                src_file = os.path.join(self.data_dir, f"completed_{session_id}.json")
                if os.path.exists(src_file):
                    # Create archive directory if needed
                    archive_dir = os.path.join(self.data_dir, "archive")
                    os.makedirs(archive_dir, exist_ok=True)
                    
                    # Move file to archive
                    dst_file = os.path.join(archive_dir, f"completed_{session_id}.json")
                    try:
                        os.rename(src_file, dst_file)
                        logger.info(f"Archived game session {session_id}")
                    except Exception as e:
                        logger.error(f"Error archiving session {session_id}: {e}")
        
        # Remove sessions from memory
        for session_id in sessions_to_remove:
            self.active_games.pop(session_id, None)
            
        logger.info(f"Cleaned up {len(sessions_to_remove)} inactive game sessions")
        return len(sessions_to_remove)
    
    def get_game_state(self, session_id: str, include_history: bool = False) -> Dict[str, Any]:
        """
        Get the current state of a game in a format suitable for display.
        
        Args:
            session_id: Game session ID
            include_history: Whether to include full move history
            
        Returns:
            Dictionary with game state information
        """
        # Get the game session
        session = self.get_game(session_id)
        if session is None:
            return {"success": False, "error": "Game session not found"}
        
        # Basic game information
        game_info = {
            "success": True,
            "session_id": session.session_id,
            "user_id": session.user_id,
            "platform": session.platform,
            "user_color": "white" if session.user_color == PieceColor.WHITE else "black",
            "difficulty": session.difficulty,
            "active_color": "white" if session.state.active_color == PieceColor.WHITE else "black",
            "moves_played": session.moves_played,
            "is_user_turn": session.state.active_color == session.user_color,
            "is_check": session.state.is_check(),
            "is_checkmate": session.state.is_checkmate(),
            "is_stalemate": session.state.is_stalemate(),
            "is_active": session.is_active,
            "outcome": session.outcome,
            "outcome_reason": session.outcome_reason,
            "fen": session.state.get_fen()
        }
        
        # Include board representation
        board_rep = []
        for y in range(7, -1, -1):  # Start from top rank (7) down to bottom rank (0)
            rank = []
            for x in range(8):  # Files from a to h (0 to 7)
                piece = session.state.get_piece_at(x, y)
                if piece:
                    rank.append(str(piece))  # Use the string representation of the piece
                else:
                    rank.append(".")  # Empty square
            board_rep.append(rank)
        
        game_info["board"] = board_rep
        
        # Include last move if any moves have been played
        if session.move_history:
            game_info["last_move"] = session.move_history[-1]
            
        # Include full history if requested
        if include_history:
            game_info["move_history"] = session.move_history
            
        return game_info
    
    def get_board_ascii(self, session_id: str) -> str:
        """
        Get an ASCII representation of the current board state.
        
        Args:
            session_id: Game session ID
            
        Returns:
            ASCII string representation of the board
        """
        session = self.get_game(session_id)
        if session is None:
            return "Game not found"
            
        # Create ASCII board
        board_str = "    a b c d e f g h\n"
        board_str += "  +-----------------+\n"
        
        for y in range(7, -1, -1):
            board_str += f"{y+1} | "
            for x in range(8):
                piece = session.state.get_piece_at(x, y)
                if piece:
                    board_str += str(piece) + " "
                else:
                    board_str += ". "
            board_str += f"| {y+1}\n"
            
        board_str += "  +-----------------+\n"
        board_str += "    a b c d e f g h\n"
        
        # Add turn indicator
        turn = "White" if session.state.active_color == PieceColor.WHITE else "Black"
        board_str += f"\nTurn: {turn}"
        
        # Add check/checkmate/stalemate indicators
        if session.state.is_checkmate():
            board_str += " (Checkmate!)"
        elif session.state.is_check():
            board_str += " (Check!)"
        elif session.state.is_stalemate():
            board_str += " (Stalemate!)"
            
        return board_str

