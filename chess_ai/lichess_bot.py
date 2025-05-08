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
from typing import Dict, Any, Optional, List, Tuple
from dotenv import load_dotenv
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("lichess_bot")

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
        self.client = berserk.Client(berserk.TokenSession(self.token))
        
        # Game state tracking
        self.current_games = {}
        self.accepted_variants = ["standard", "chess960", "crazyhouse", "antichess", "atomic"]
        self.ai_engine = None  # Will be set later
        
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
            self.client.board.make_move(game_id, move)
            logger.info(f"Made move {move} in game {game_id}")
            return True
        except berserk.exceptions.ResponseError as e:
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
            self.client.board.resign_game(game_id)
            logger.info(f"Resigned game {game_id}")
            return True
        except berserk.exceptions.ResponseError as e:
            logger.error(f"Failed to resign game {game_id}: {e}")
            return False
            
    def process_challenge_event(self, event: Dict[str, Any]) -> None:
        """
        Process a challenge event from Lichess.
        
        Args:
            event: Challenge event data from Lichess
        """
        challenge = event['challenge']
        challenge_id = challenge['id']
        
        # Extract relevant challenge info
        variant = challenge.get('variant', {}).get('key', 'standard')
        rated = challenge.get('rated', False)
        opponent = challenge.get('challenger', {}).get('name', 'Unknown')
        
        # Check if we want to accept this challenge
        if variant in self.accepted_variants:
            logger.info(f"Accepting challenge from {opponent} ({variant})")
            self.accept_challenge(challenge_id)
        else:
            logger.info(f"Declining challenge from {opponent} (unsupported variant: {variant})")
            self.decline_challenge(challenge_id, reason="variant")
            
    def process_game_event(self, event: Dict[str, Any], game_state: Dict[str, Any]) -> None:
        """
        Process a game state event from Lichess.
        
        Args:
            event: Game event data from Lichess
            game_state: Current game state
        """
        game_id = game_state['id']
        
        # Check if it's our turn
        if game_state.get('isMyTurn', False):
            # Convert game state to a chess board
            board = chess.Board(game_state.get('fen', chess.STARTING_FEN))
            
            # Use AI engine to generate a move
            if self.ai_engine is not None:
                try:
                    # For compatibility with ChessState, we'd need to convert chess.Board to ChessState
                    # This is a placeholder - actual implementation would depend on AI engine's interface
                    chess_state = self._convert_to_chess_state(board)
                    best_move = self.ai_engine.get_best_move(chess_state)
                    
                    if best_move:
                        # Convert move to UCI format
                        from_x, from_y = best_move[0]
                        to_x, to_y = best_move[1]
                        
                        # Convert to UCI coordinates (e.g., "e2e4")
                        files = "abcdefgh"
                        ranks = "12345678"
                        
                        uci_move = f"{files[from_x]}{ranks[from_y]}{files[to_x]}{ranks[to_y]}"
                        self.make_move(game_id, uci_move)
                    else:
                        # No legal moves - should mean game is over
                        logger.info(f"No legal moves in game {game_id}")
                except Exception as e:
                    logger.error(f"Error generating or making move: {e}")
                    # If there's a problem, resign the game
                    self.resign_game(game_id)
            else:
                logger.error("No AI engine connected to generate moves")
                self.resign_game(game_id)
                
    def _convert_to_chess_state(self, board: chess.Board):
        """
        Convert python-chess Board to the project's ChessState.
        
        This is a placeholder method that should be implemented based on
        the actual ChessState implementation in the project.
        
        Args:
            board: A python-chess Board object
            
        Returns:
            A ChessState object representing the same position
        """
        # This is a placeholder - actual implementation would depend on ChessState's interface
        # The implementation would need to set up the board position, active color, castling rights, etc.
        raise NotImplementedError("This method needs to be implemented based on ChessState's interface")
        
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
            for event in self.client.board.stream_incoming_events():
                if event['type'] == 'challenge':
                    self.process_challenge_event(event)
                elif event['type'] == 'gameStart':
                    # A game has started - we now need to stream the game state
                    game_id = event['game']['id']
                    logger.info(f"Game started: {game_id}")
                    
                    # Start a new thread to handle this game
                    # In a production bot, we would use proper threading/async
                    # This is just a placeholder for demonstration
                    self._handle_game(game_id)
        except berserk.exceptions.ResponseError as e:
            logger.error(f"Error in bot event loop: {e}")
        except KeyboardInterrupt:
            logger.info("Bot event loop terminated by user")
            
    def _handle_game(self, game_id: str) -> None:
        """
        Handle a single game's events and moves.
        
        Args:
            game_id: ID of the game to handle
        """
        try:
            # Stream the game state and make moves when it's our turn
            for game_state in self.client.board.stream_game_state(game_id):
                self.process_game_event(None, game_state)  # None for event since it's included in game_state
                
                # Check if game is over
                if game_state.get('status') != 'started':
                    logger.info(f"Game {game_id} ended with status: {game_state.get('status', 'unknown')}")
                    break
        except berserk.exceptions.ResponseError as e:
            logger.error(f"Error handling game {game_id}: {e}")


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

