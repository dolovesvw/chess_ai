#!/usr/bin/env python3
"""
Lichess Bot Runner

This module connects the chess AI engine to the Lichess API,
allowing the AI to play games on Lichess.org through the bot interface.
"""

import os
import sys
import time
import logging
import chess
import threading
from pathlib import Path
from dotenv import load_dotenv

from .ai_engine import ChessAI
from .state_manager import ChessState, PieceType, PieceColor
from .lichess_bot import LichessBot

# Import logging but don't configure it here since lichess_bot.py already sets up logging
logger = logging.getLogger("bot_runner")

# Load environment variables from .env file
load_dotenv()


class ChessStateConverter:
    """
    Utility class to convert between python-chess Board objects and
    our ChessState objects for use with ChessAI.
    """
    
    @staticmethod
    def python_chess_to_chess_state(board: chess.Board) -> ChessState:
        """
        Convert a python-chess Board to our ChessState object.
        
        Args:
            board: A python-chess Board instance
            
        Returns:
            A ChessState object representing the same position
        """
        chess_state = ChessState()
        
        # Clear the board first
        chess_state.board = {}
        
        # Map the active color
        chess_state.active_color = PieceColor.WHITE if board.turn else PieceColor.BLACK
        
        # Iterate through all squares and add pieces
        for square in chess.SQUARES:
            piece = board.piece_at(square)
            if piece:
                # Get coordinates in our format (0-7 range)
                file = chess.square_file(square)
                rank = chess.square_rank(square)
                
                # Map piece type
                piece_type = None
                if piece.piece_type == chess.PAWN:
                    piece_type = PieceType.PAWN
                elif piece.piece_type == chess.KNIGHT:
                    piece_type = PieceType.KNIGHT
                elif piece.piece_type == chess.BISHOP:
                    piece_type = PieceType.BISHOP
                elif piece.piece_type == chess.ROOK:
                    piece_type = PieceType.ROOK
                elif piece.piece_type == chess.QUEEN:
                    piece_type = PieceType.QUEEN
                elif piece.piece_type == chess.KING:
                    piece_type = PieceType.KING
                
                # Map piece color
                color = PieceColor.WHITE if piece.color else PieceColor.BLACK
                
                # Set piece on our board
                from .state_manager import ChessPiece
                chess_state.board[(file, rank)] = ChessPiece(piece_type, color)
        
        # Set en passant target, if any
        if board.ep_square is not None:
            file = chess.square_file(board.ep_square)
            rank = chess.square_rank(board.ep_square)
            chess_state.en_passant_target = (file, rank)
        else:
            chess_state.en_passant_target = None
        
        # Set castling rights - basic for now
        chess_state.castling_rights = {
            PieceColor.WHITE: (board.has_queenside_castling_rights(chess.WHITE), 
                             board.has_kingside_castling_rights(chess.WHITE)),
            PieceColor.BLACK: (board.has_queenside_castling_rights(chess.BLACK), 
                             board.has_kingside_castling_rights(chess.BLACK))
        }
        
        # Set move counters
        chess_state.halfmove_clock = board.halfmove_clock
        chess_state.fullmove_number = board.fullmove_number
        
        return chess_state
    
    @staticmethod
    def chess_move_to_uci(move: tuple) -> str:
        """
        Convert our move format ((from_x, from_y), (to_x, to_y)) to UCI format.
        
        Args:
            move: A move as ((from_x, from_y), (to_x, to_y))
            
        Returns:
            The move in UCI format (e.g., "e2e4")
        """
        if move is None:
            return None
            
        from_pos, to_pos = move
        from_x, from_y = from_pos
        to_x, to_y = to_pos
        
        # Convert to algebraic notation
        files = "abcdefgh"
        ranks = "12345678"
        
        from_sq = files[from_x] + ranks[from_y]
        to_sq = files[to_x] + ranks[to_y]
        
        return from_sq + to_sq


class LichessBotRunner:
    """
    Main class for running the chess bot on Lichess.org.
    
    Handles the connection between our ChessAI engine and the LichessBot interface.
    """
    
    def __init__(self, difficulty: int = 3, token: str = None):
        """
        Initialize the Lichess Bot Runner.
        
        Args:
            difficulty: AI difficulty level (1-5)
            token: Lichess API token (if None, loads from environment)
        """
        self.ai_engine = ChessAI(difficulty=difficulty)
        self.lichess_bot = LichessBot(token=token)
        
        # Connect the two components
        self.lichess_bot._convert_to_chess_state = self._convert_to_chess_state
        
        # Set up a callback for game start events
        self.lichess_bot.on_game_start = self._on_game_start
        
        # Track active games and their threads
        self.active_games = {}
        self.game_threads = {}
        
        # Lock for thread safety when modifying game collections
        self.games_lock = threading.Lock()
        
    def _convert_to_chess_state(self, board: chess.Board) -> ChessState:
        """
        Convert python-chess Board to ChessState for our AI.
        
        Args:
            board: A python-chess Board
            
        Returns:
            A ChessState representation
        """
        return ChessStateConverter.python_chess_to_chess_state(board)
    
    def start(self):
        """
        Start the Lichess bot. This will connect to Lichess API and begin
        listening for and handling game events.
        """
        # Connect the AI engine to the bot
        self.lichess_bot.connect_ai_engine(self.ai_engine)
        
        # Validate token and connection
        if not self.lichess_bot.validate_token():
            logger.error("Failed to validate Lichess API token. Please check your token.")
            return False
        
        # Start the main event loop
        try:
            self.lichess_bot.start_bot_loop()
        except KeyboardInterrupt:
            logger.info("Bot stopped by user")
        except Exception as e:
            logger.error(f"Error in bot loop: {e}")
        
        return True
    
    def _on_game_start(self, game_id, game_data):
        """
        Callback for when a new game starts.
        
        Args:
            game_id: Lichess game ID
            game_data: Initial game data
        """
        logger.info(f"Starting new game: {game_id}")
        
        # Track the game in our active games
        with self.games_lock:
            self.active_games[game_id] = {
                'id': game_id,
                'data': game_data,
                'start_time': time.time()
            }
            
            # Start a new thread to handle this game
            game_thread = threading.Thread(
                target=self.play_game,
                args=(game_id,),
                name=f"game-{game_id}"
            )
            game_thread.daemon = True  # Make thread exit when main thread exits
            self.game_threads[game_id] = game_thread
            game_thread.start()
            
    def _end_game(self, game_id, status="finished"):
        """
        Clean up after a game ends.
        
        Args:
            game_id: Lichess game ID
            status: Final game status
        """
        logger.info(f"Game {game_id} ended with status: {status}")
        
        # Remove from active games and threads
        with self.games_lock:
            if game_id in self.active_games:
                del self.active_games[game_id]
            if game_id in self.game_threads:
                # Thread will terminate naturally, we just remove the reference
                del self.game_threads[game_id]
    
    def play_game(self, game_id):
        """
        Handle an individual game in a separate thread.
        
        Args:
            game_id: Lichess game ID to play
        """
        try:
            logger.info(f"Game thread started for game {game_id}")
            
            # Store our color for this game when we find out what it is
            our_color = None
            
            # Stream game state
            for game_state in self.lichess_bot.stream_bot_game(game_id):
                try:
                    logger.debug(f"Received game state: {game_state}")
                    
                    # Check if there's an error in the stream
                    if "error" in game_state:
                        logger.error(f"Stream error in game {game_id}: {game_state['error']}")
                        self._end_game(game_id, "error")
                        break
                    
                    # Check if the game has ended
                    status = game_state.get("status")
                    if status and status != "started" and status != "created":
                        logger.info(f"Game {game_id} ended with status: {status}")
                        self._end_game(game_id, status)
                        break
                        
                    # Process different types of game states
                    state_type = game_state.get("type")
                    
                    if state_type == "gameFull":
                        # Initial game state
                        logger.info(f"Received full game state for game {game_id}")
                        
                        # Determine our color
                        account_id = self.lichess_bot.client.account.get()['id']
                        if game_state.get('white', {}).get('id') == account_id:
                            our_color = 'white'
                        else:
                            our_color = 'black'
                        logger.info(f"We are playing as {our_color} in game {game_id}")
                        
                        # Store game info
                        with self.games_lock:
                            if game_id in self.active_games:
                                self.active_games[game_id]['data'] = game_state
                                self.active_games[game_id]['color'] = our_color
                        
                        # Extract important state info from the nested structure
                        inner_state = game_state.get('state', {})
                        if inner_state:
                            # Check if it's our turn using moves
                            moves = inner_state.get('moves', '').split()
                            is_our_turn = (our_color == 'white' and len(moves) % 2 == 0) or \
                                          (our_color == 'black' and len(moves) % 2 == 1)
                            
                            if is_our_turn:
                                logger.info(f"It's our turn in game {game_id}")
                                # Create composite state with needed info
                                composite_state = {
                                    'type': 'gameState',
                                    'moves': inner_state.get('moves', ''),
                                    'status': inner_state.get('status', 'started'),
                                    'color': our_color,
                                    'initialFen': game_state.get('initialFen', 'startpos')
                                }
                                self._make_ai_move(game_id, composite_state)
                    
                    elif state_type == "gameState":
                        # Game state update
                        # Use our stored color if available
                        with self.games_lock:
                            if game_id in self.active_games and 'color' in self.active_games[game_id]:
                                our_color = self.active_games[game_id]['color']
                        
                        if our_color:
                            # Check if it's our turn using moves
                            moves = game_state.get('moves', '').split()
                            is_our_turn = (our_color == 'white' and len(moves) % 2 == 0) or \
                                          (our_color == 'black' and len(moves) % 2 == 1)
                            
                            if is_our_turn:
                                logger.info(f"It's our turn in game {game_id}")
                                # Add color to game state for our internal use
                                game_state['color'] = our_color
                                self._make_ai_move(game_id, game_state)
                        else:
                            logger.warning(f"Received game state but don't know our color for game {game_id}")
                
                except Exception as state_error:
                    logger.error(f"Error processing game state in game {game_id}: {state_error}")
                    # Continue processing the game rather than exiting
            
        except Exception as e:
            logger.error(f"Error handling game {game_id}: {e}")
            # If there's a problem, resign the game
            try:
                self.lichess_bot.resign_game(game_id)
            except Exception as resign_error:
                logger.error(f"Failed to resign game {game_id}: {resign_error}")
            finally:
                self._end_game(game_id, "error")
                
    def _is_my_turn(self, game_state):
        """
        Determine if it's our turn to make a move based on the game state.
        
        Args:
            game_state: Current game state from Lichess API
            
        Returns:
            True if it's our turn, False otherwise
        """
        # Handle different game state types
        if game_state.get('type') == 'gameFull':
            # For full game data
            state = game_state.get('state', {})
            our_color = game_state.get('white', {}).get('id') == self.lichess_bot.client.account.get()['id']
            moves = state.get('moves', '').split()
            
            # If no moves yet and we're white, or odd number of moves and we're black
            return (not moves and our_color) or (len(moves) % 2 == 1 and not our_color)
            
        elif game_state.get('type') == 'gameState':
            # For game state updates
            moves = game_state.get('moves', '').split()
            color = game_state.get('color', 'white')  # Our color in this game
            
            # If we're white, it's our turn on even number of moves (including 0)
            # If we're black, it's our turn on odd number of moves
            if color == 'white':
                return len(moves) % 2 == 0
            else:
                return len(moves) % 2 == 1
                
        # If we can't determine, assume it's not our turn
        return False
        
    def _make_ai_move(self, game_id, game_state):
        """
        Use the AI engine to generate and make a move.
        
        Args:
            game_id: ID of the current game
            game_state: Current game state from Lichess API
        """
        try:
            # Extract FEN position
            if game_state.get('type') == 'gameFull':
                fen = game_state.get('initialFen', chess.STARTING_FEN)
                if fen == 'startpos':
                    fen = chess.STARTING_FEN
                    
                # Apply any moves that have been made
                moves = game_state.get('state', {}).get('moves', '').split()
            else:
                fen = game_state.get('fen', chess.STARTING_FEN)
                moves = game_state.get('moves', '').split()
                
            # Create a board with the current position
            board = chess.Board(fen)
            
            # Apply all moves to get to current position
            for move in moves:
                board.push_uci(move)
                
            # Convert to our chess state format
            chess_state = self._convert_to_chess_state(board)
            
            # Get best move from AI
            best_move = self.ai_engine.get_best_move(chess_state)
            
            if best_move:
                # Convert to UCI format
                uci_move = ChessStateConverter.chess_move_to_uci(best_move)
                
                # Make the move
                success = self.lichess_bot.make_move(game_id, uci_move)
                if success:
                    logger.info(f"Made move {uci_move} in game {game_id}")
                else:
                    logger.warning(f"Failed to make move {uci_move} in game {game_id}")
            else:
                # No legal moves - should mean game is over or we're in a stalemate
                logger.info(f"No legal moves found in game {game_id}")
                self.lichess_bot.resign_game(game_id)
                
        except Exception as e:
            logger.error(f"Error generating or making move: {e}")
            # If there's a problem, resign the game
            self.lichess_bot.resign_game(game_id)


def main():
    """
    Main entry point for the Lichess bot runner.
    
    Sets up and runs the bot with command line arguments.
    """
    import argparse
    
    parser = argparse.ArgumentParser(description="Run a Chess AI bot on Lichess.org")
    parser.add_argument("--difficulty", type=int, default=3, choices=range(1, 6),
                        help="Difficulty level of the AI (1-5)")
    parser.add_argument("--token", type=str, default=None,
                        help="Lichess API token (will use LICHESS_API_TOKEN env var if not provided)")
    
    args = parser.parse_args()
    
    # Create and start the bot
    bot_runner = LichessBotRunner(difficulty=args.difficulty, token=args.token)
    bot_runner.start()


if __name__ == "__main__":
    main()

