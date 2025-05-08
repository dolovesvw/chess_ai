#!/usr/bin/env python3
"""
Lichess Bot Module

This module handles all Lichess.org API communication for the chess AI bot,
including account setup, game interactions, and move synchronization.
"""

import os
import sys
import time
import logging
import chess
import requests
import berserk
import json
import threading
from typing import Dict, Any, Optional, List, Tuple, Iterator, Callable
from dotenv import load_dotenv
from pathlib import Path
from logging.handlers import RotatingFileHandler
import datetime

# Create logs directory if it doesn't exist
logs_dir = Path("logs")
logs_dir.mkdir(exist_ok=True)

# Configure logging
def setup_logging():
    """Set up logging to both console and file."""
    # Create logger
    logger = logging.getLogger("lichess_bot")
    logger.setLevel(logging.DEBUG)
    
    # Create formatters
    file_formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s"
    )
    console_formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    
    # Create console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(console_formatter)
    
    # Create file handler
    log_file = logs_dir / f"lichess_bot_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
    file_handler = RotatingFileHandler(
        log_file, 
        maxBytes=10 * 1024 * 1024,  # 10 MB
        backupCount=5
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(file_formatter)
    
    # Add handlers to logger
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)
    
    logger.info(f"Logging initialized. Log file: {log_file}")
    return logger

# Set up logger
logger = setup_logging()

# Load environment variables from .env file
load_dotenv()


class LichessBot:
    """
    Handles Lichess API interactions for a chess bot.
    
    This class provides methods for connecting to Lichess.org, upgrading
    an account to a bot account, accepting challenges, and playing games.
    """
    
    def __init__(self, token: Optional[str] = None):
        """
        Initialize the Lichess bot with API token.
        
        Args:
            token: Lichess API token (if None, loads from environment variable)
        """
        self.token = token or os.getenv("LICHESS_API_TOKEN")
        if not self.token:
            raise ValueError("Lichess API token not provided and LICHESS_API_TOKEN not set in environment")
            
        # Initialize the Lichess API client
        self.session = requests.Session()
        self.session.headers.update({"Authorization": f"Bearer {self.token}"})
        
        # Initialize berserk client
        session = berserk.TokenSession(self.token)
        self.client = berserk.Client(session)
        
        # Game state tracking
        self.current_games = {}
        self.current_games_lock = threading.Lock()
        self.accepted_variants = ["standard", "chess960", "crazyhouse", "antichess", "atomic"]
        self.ai_engine = None  # Will be set later
        
        # Callback for game start events (will be set by LichessBotRunner)
        self._on_game_start = None
        
        # Game threads - to track and manage game handling threads
        self.game_threads = {}
        self.game_threads_lock = threading.Lock()
        
        # Request timeout in seconds
        self.request_timeout = 30
    
    @property
    def on_game_start(self) -> Optional[Callable[[str, Dict[str, Any]], None]]:
        """
        Get the callback function for game start events.
        
        Returns:
            The callback function or None if not set
        """
        return self._on_game_start
        
    @on_game_start.setter
    def on_game_start(self, callback: Optional[Callable[[str, Dict[str, Any]], None]]) -> None:
        """
        Set the callback function for game start events.
        
        Args:
            callback: A function that takes game_id (str) and game_data (dict) arguments,
                      or None to remove the callback
                      
        Raises:
            TypeError: If callback is not callable (when not None)
        """
        if callback is not None and not callable(callback):
            raise TypeError("on_game_start callback must be callable or None")
        self._on_game_start = callback
        
    def validate_token(self) -> bool:
        """
        Validate that the API token is working.
        
        Returns:
            True if the token is valid, False otherwise
        """
        try:
            account_info = self.client.account.get()
            logger.info(f"Connected to Lichess as: {account_info.get('username', 'Unknown')}")
            return True
        except berserk.exceptions.ResponseError as e:
            logger.error(f"Invalid API token or connection error: {e}")
            return False
            
    def upgrade_to_bot(self) -> bool:
        """
        Upgrade the account associated with the token to a BOT account.
        
        This is irreversible and can only be done on accounts that haven't played games.
        
        Returns:
            True if successful, False otherwise
        """
        try:
            # First check if already a bot
            account_info = self.client.account.get()
            if account_info.get('bot', False):
                logger.info("Account is already a BOT account")
                return True
                
            # Direct API call because berserk doesn't have a dedicated method for this
            response = self.session.post("https://lichess.org/api/bot/account/upgrade")
            
            if response.status_code == 200:
                logger.info("Successfully upgraded to BOT account")
                return True
            else:
                logger.error(f"Failed to upgrade to BOT account: {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"Error upgrading to BOT account: {e}")
            return False
            
    def connect_ai_engine(self, ai_engine):
        """
        Connect the chess AI engine to this bot.
        
        Args:
            ai_engine: An instance of the chess AI engine
        """
        self.ai_engine = ai_engine
        logger.info("AI engine connected to Lichess bot")
        
    def accept_challenge(self, challenge_id: str) -> bool:
        """
        Accept a challenge from another Lichess player.
        
        Args:
            challenge_id: ID of the challenge to accept
            
        Returns:
            True if successful, False otherwise
        """
        try:
            self.client.challenges.accept(challenge_id)
            logger.info(f"Accepted challenge: {challenge_id}")
            return True
        except berserk.exceptions.ResponseError as e:
            logger.error(f"Failed to accept challenge {challenge_id}: {e}")
            return False
            
    def decline_challenge(self, challenge_id: str, reason: str = "generic") -> bool:
        """
        Decline a challenge from another Lichess player.
        
        Args:
            challenge_id: ID of the challenge to decline
            reason: Reason for declining (e.g., "generic", "later", "tooFast", "tooSlow")
            
        Returns:
            True if successful, False otherwise
        """
        try:
            self.client.challenges.decline(challenge_id, reason=reason)
            logger.info(f"Declined challenge: {challenge_id} (reason: {reason})")
            return True
        except berserk.exceptions.ResponseError as e:
            logger.error(f"Failed to decline challenge {challenge_id}: {e}")
            return False
            
    def make_move(self, game_id: str, move: str) -> bool:
        """
        Make a move in an ongoing game.
        
        Args:
            game_id: ID of the game
            move: Move in UCI format (e.g., "e2e4")
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Direct API call because berserk.client.bot.make_move might not be fully implemented
            response = self.session.post(f"https://lichess.org/api/bot/game/{game_id}/move/{move}")
            
            if response.status_code == 200:
                logger.info(f"Made move {move} in game {game_id}")
                return True
            else:
                logger.error(f"Failed to make move {move} in game {game_id}: {response.text}")
                return False
        except Exception as e:
            logger.error(f"Failed to make move {move} in game {game_id}: {e}")
            return False
            
    def resign_game(self, game_id: str) -> bool:
        """
        Resign from an ongoing game.
        
        Args:
            game_id: ID of the game to resign from
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Direct API call because berserk.client.bot.resign_game might not be fully implemented
            response = self.session.post(f"https://lichess.org/api/bot/game/{game_id}/resign")
            
            if response.status_code == 200:
                logger.info(f"Resigned game {game_id}")
                return True
            else:
                logger.error(f"Failed to resign game {game_id}: {response.text}")
                return False
        except Exception as e:
            logger.error(f"Failed to resign game {game_id}: {e}")
            return False
            
    def process_challenge_event(self, event: Dict[str, Any]) -> None:
        """
        Process a challenge event from Lichess.
        
        Args:
            event: Challenge event data from Lichess
        """
        try:
            # Log full challenge event data for debugging
            logger.debug(f"Received challenge event: {event}")
            
            challenge = event['challenge']
            challenge_id = challenge['id']
            
            # Extract detailed challenge info
            variant = challenge.get('variant', {}).get('key', 'standard')
            rated = challenge.get('rated', False)
            opponent = challenge.get('challenger', {}).get('name', 'Unknown')
            opponent_id = challenge.get('challenger', {}).get('id', 'Unknown')
            opponent_rating = challenge.get('challenger', {}).get('rating', 0)
            time_control = challenge.get('timeControl', {})
            color = challenge.get('color', 'random')
            
            # Log detailed challenge information
            logger.info(f"Challenge received: ID={challenge_id}, Opponent={opponent} (Rating: {opponent_rating})")
            logger.info(f"Challenge details: Variant={variant}, Rated={rated}, Color={color}")
            logger.info(f"Time control: {time_control}")
            
            # Check if we want to accept this challenge
            if variant in self.accepted_variants:
                logger.info(f"Accepting challenge from {opponent} ({variant})")
                try:
                    accept_result = self.accept_challenge(challenge_id)
                    logger.info(f"Challenge {challenge_id} acceptance result: {accept_result}")
                except Exception as e:
                    logger.error(f"Error accepting challenge {challenge_id}: {e}")
            else:
                logger.info(f"Declining challenge from {opponent} (unsupported variant: {variant})")
                try:
                    decline_result = self.decline_challenge(challenge_id, reason="variant")
                    logger.info(f"Challenge {challenge_id} decline result: {decline_result}")
                except Exception as e:
                    logger.error(f"Error declining challenge {challenge_id}: {e}")
        except KeyError as e:
            logger.error(f"Missing key in challenge event data: {e}")
            logger.debug(f"Challenge event data: {event}")
        except Exception as e:
            logger.error(f"Error processing challenge event: {e}")
            logger.debug(f"Challenge event data: {event}")
            
    def process_game_event(self, event: Dict[str, Any], game_state: Dict[str, Any]) -> None:
        """
        Process a game state event from Lichess.
        
        Args:
            event: Game event data from Lichess
            game_state: Current game state
        """
        # Process different types of game state events
        if game_state.get('type') == 'gameFull':
            # Initial game state
            game_id = game_state['id']
            
            # Check if it's already our turn
            state = game_state.get('state', {})
            if self._is_my_turn(game_state):
                self._make_ai_move(game_id, state)
        
        elif game_state.get('type') == 'gameState':
            # Game state update
            if 'id' in game_state:
                game_id = game_state['id']
            else:
                # Find game_id from a previous state
                game_id = next(iter(self.current_games.keys())) if self.current_games else None
                if not game_id:
                    logger.error("Cannot determine game ID from game state update")
                    return
                    
            # Check if it's our turn
            if self._is_my_turn(game_state):
                self._make_ai_move(game_id, game_state)
    
    def _is_my_turn(self, game_state: Dict[str, Any]) -> bool:
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
            our_color = game_state.get('white', {}).get('id') == self.client.account.get()['id']
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
        
    def _make_ai_move(self, game_id: str, game_state: Dict[str, Any]) -> None:
        """
        Use the AI engine to generate and make a move.
        
        Args:
            game_id: ID of the current game
            game_state: Current game state from Lichess API
        """
        if self.ai_engine is None:
            logger.error("No AI engine connected to generate moves")
            self.resign_game(game_id)
            return
            
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
                # Convert move to UCI format
                from_pos, to_pos = best_move
                from_x, from_y = from_pos
                to_x, to_y = to_pos
                
                # Convert to UCI coordinates (e.g., "e2e4")
                files = "abcdefgh"
                ranks = "12345678"
                
                uci_move = f"{files[from_x]}{ranks[from_y]}{files[to_x]}{ranks[to_y]}"
                
                # Make the move
                self.make_move(game_id, uci_move)
            else:
                # No legal moves - should mean game is over or we're in a stalemate
                logger.info(f"No legal moves found in game {game_id}")
                self.resign_game(game_id)
                
        except Exception as e:
            logger.error(f"Error generating or making move: {e}")
            # If there's a problem, resign the game
            self.resign_game(game_id)
    def _convert_to_chess_state(self, board: chess.Board):
        """
        Convert python-chess Board to the project's ChessState.
        
        Uses the ChessStateConverter from bot_runner to perform the conversion.
        
        Args:
            board: A python-chess Board object
            
        Returns:
            A ChessState object representing the same position
        """
        from .bot_runner import ChessStateConverter
        return ChessStateConverter.python_chess_to_chess_state(board)
        
    def stream_bot_game(self, game_id: str):
        """
        Stream a bot game state directly using the requests session.
        
        Args:
            game_id: ID of the game to stream
            
        Yields:
            Dict containing game state updates
        """
        try:
            # Use the bot-specific endpoint for game streaming
            url = f"https://lichess.org/api/bot/game/stream/{game_id}"
            response = self.session.get(url, stream=True, timeout=self.request_timeout)
            
            if response.status_code != 200:
                logger.error(f"Failed to connect to game stream for game {game_id}: {response.text}")
                yield {"error": f"Connection error: {response.status_code}", "status": "aborted"}
                return
            
            import json
            for line in response.iter_lines():
                if not line:
                    continue
                    
                try:
                    game_state = json.loads(line.decode('utf-8'))
                    yield game_state
                except json.JSONDecodeError as e:
                    logger.error(f"Error parsing game state data: {e}")
                    continue
                except Exception as e:
                    logger.error(f"Error processing game state data: {e}")
                    continue
                    
        except requests.exceptions.RequestException as e:
            logger.error(f"Network error in game stream: {e}")
            yield {"error": f"Network error: {str(e)}", "status": "aborted"}
        except Exception as e:
            logger.error(f"Unexpected error in game stream: {e}")
            yield {"error": f"Unexpected error: {str(e)}", "status": "aborted"}
        
    def start_bot_loop(self) -> None:
        """
        Start the bot's main event loop to listen for challenges and game events.
        
        This method will block indefinitely, processing events as they come in.
        """
        if self.ai_engine is None:
            logger.error("No AI engine connected - connect an engine before starting the bot loop")
            return
            
        logger.info("Starting Lichess bot event loop")
        
        try:
            # Listen for incoming events from Lichess
            # Stream from /api/stream/event endpoint
            response = self.session.get("https://lichess.org/api/stream/event", stream=True)
            
            if response.status_code != 200:
                logger.error(f"Failed to connect to event stream: {response.text}")
                return
                
            for line in response.iter_lines():
                if not line:
                    continue
                    
                import json
                event = json.loads(line.decode('utf-8'))
                
                if event['type'] == 'challenge':
                    self.process_challenge_event(event)
                elif event['type'] == 'gameStart':
                    # A game has started - we now need to stream the game state
                    game_id = event['game']['id']
                    game_data = event.get('game', {})
                    logger.info(f"Game started: {game_id}")
                    
                    # Call the callback if set (will let LichessBotRunner handle the game)
                    if self.on_game_start is not None:
                        logger.debug(f"Using external game handler for game {game_id}")
                        self.on_game_start(game_id, game_data)
                    else:
                        # Use internal handling if no callback is set
                        logger.debug(f"Using internal game handler for game {game_id}")
                        # Start a new thread to handle this game
                        game_thread = threading.Thread(
                            target=self._handle_game,
                            args=(game_id,),
                            name=f"game-{game_id}"
                        )
                        game_thread.daemon = True
                        self.game_threads[game_id] = game_thread
                        game_thread.start()
        except requests.exceptions.RequestException as e:
            logger.error(f"Error in bot event loop: {e}")
        except KeyboardInterrupt:
            logger.info("Bot event loop terminated by user")
        except json.JSONDecodeError as e:
            logger.error(f"Error parsing event stream data: {e}")
        except Exception as e:
            logger.error(f"Unexpected error in bot event loop: {e}")
            
    def _handle_game(self, game_id: str) -> None:
        """
        Handle a single game's events and moves.
        
        Args:
            game_id: ID of the game to handle
        """
        # Store the game in our current games dictionary
        self.current_games[game_id] = {
            'id': game_id,
            'status': 'started',
            'start_time': time.time()
        }
        
        try:
            logger.info(f"Starting game handler thread for game {game_id}")
            
            # Stream the game state and make moves when it's our turn
            # Use the bot game stream endpoint
            response = self.session.get(f"https://lichess.org/api/bot/game/stream/{game_id}", stream=True)
            
            if response.status_code != 200:
                logger.error(f"Failed to connect to game stream for game {game_id}: {response.text}")
                self._end_game(game_id, "connection_error")
                return
                
            import json
            for line in response.iter_lines():
                if not line:
                    continue
                
                try:
                    game_state = json.loads(line.decode('utf-8'))
                    
                    # Update game state in our tracking dictionary
                    if game_id in self.current_games:
                        if 'state' not in self.current_games[game_id]:
                            self.current_games[game_id]['state'] = {}
                        
                        # Update with latest state info
                        if game_state.get('type') == 'gameFull':
                            self.current_games[game_id]['state'] = game_state.get('state', {})
                            # Store other game info like colors, players, etc.
                            self.current_games[game_id]['white'] = game_state.get('white', {})
                            self.current_games[game_id]['black'] = game_state.get('black', {})
                        elif game_state.get('type') == 'gameState':
                            # Update just the state portion
                            self.current_games[game_id]['state'].update(game_state)
                    
                    # Process the game event
                    self.process_game_event(None, game_state)
                    
                    # Check if game is over
                    status = game_state.get('status')
                    if status and status != 'started':
                        logger.info(f"Game {game_id} ended with status: {status}")
                        self._end_game(game_id, status)
                        break
                except json.JSONDecodeError as e:
                    logger.error(f"Error parsing game state data in game {game_id}: {e}")
                except Exception as e:
                    logger.error(f"Error processing game state in game {game_id}: {e}")
                    # Continue trying to process the game rather than exiting
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Network error handling game {game_id}: {e}")
            self._end_game(game_id, "network_error")
        except Exception as e:
            logger.error(f"Unexpected error handling game {game_id}: {e}")
            self._end_game(game_id, "error")
    
    def _end_game(self, game_id: str, status: str = "finished") -> None:
        """
        Clean up resources associated with a game that has ended.
        
        Args:
            game_id: ID of the game that ended
            status: Final status of the game
        """
        logger.info(f"Ending game {game_id} with status: {status}")
        
        # Update game status
        if game_id in self.current_games:
            self.current_games[game_id]['status'] = status
            self.current_games[game_id]['end_time'] = time.time()
            
            # Calculate game duration
            if 'start_time' in self.current_games[game_id]:
                duration = self.current_games[game_id]['end_time'] - self.current_games[game_id]['start_time']
                logger.info(f"Game {game_id} lasted {duration:.1f} seconds")
        
        # Remove thread reference
        if game_id in self.game_threads:
            del self.game_threads[game_id]


def create_bot_account():
    """
    Utility function to create a new bot account (run from command line).
    
    This function walks through the process of:
    1. Checking for an API token
    2. Upgrading the account to a BOT account
    
    It's meant to be run once when setting up a new bot.
    """
    # Check for token in environment
    token = os.getenv("LICHESS_API_TOKEN")
    
    if not token:
        print("No LICHESS_API_TOKEN found in environment variables.")
        print("Please enter your Lichess API token:")
        token = input("> ").strip()
        
        if not token:
            print("Error: No token provided. Please create a token at https://lichess.org/account/oauth/token")
            return False
    
    try:
        # Initialize bot with the token
        bot = LichessBot(token)
        
        # Validate the token
        if not bot.validate_token():
            print("Error: Invalid token or connection problem.")
            return False
        
        # Prompt for confirmation before upgrading
        print("\n*** WARNING: Upgrading to a BOT account is IRREVERSIBLE ***")
        print("The account must not have played any games.")
        print("Do you want to continue? (yes/no)")
        
        confirmation = input("> ").strip().lower()
        if confirmation != 'yes':
            print("Aborted. Account not upgraded.")
            return False
        
        # Upgrade to bot account
        if bot.upgrade_to_bot():
            print("Success! Your account is now a Lichess BOT.")
            print("You can use this account with the LichessBot class.")
            
            # Save token to .env file if not already there
            if not os.getenv("LICHESS_API_TOKEN"):
                env_path = Path('.env')
                if not env_path.exists():
                    with open(env_path, 'w') as f:
                        f.write(f"LICHESS_API_TOKEN={token}\n")
                else:
                    with open(env_path, 'a') as f:
                        f.write(f"LICHESS_API_TOKEN={token}\n")
                print("Token saved to .env file.")
                
            return True
        else:
            print("Failed to upgrade to BOT account.")
            print("Make sure the account has never played any games.")
            return False
            
    except Exception as e:
        print(f"Error: {e}")
        return False


if __name__ == "__main__":
    """
    Command-line interface for Lichess bot setup.
    
    Usage:
        python lichess_bot.py setup   # Set up a new bot account
        python lichess_bot.py run     # Run the bot (not implemented yet)
    """
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        
        if command == "setup":
            # Run the bot account setup
            success = create_bot_account()
            if success:
                print("\nBot account setup complete!")
            else:
                print("\nBot account setup failed.")
                sys.exit(1)
        elif command == "run":
            print("Bot running mode is not implemented in this basic version.")
            print("You would need to implement a proper game handling system with threads/async.")
            print("This would connect to your Chess AI engine and play games on Lichess.")
        else:
            print(f"Unknown command: {command}")
            print("Available commands: setup, run")
    else:
        print("No command specified. Available commands: setup, run")
        print("Example usage: python lichess_bot.py setup")

