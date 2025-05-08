#!/usr/bin/env python3
"""
Lichess Bot Runner Script

This script launches the Lichess bot, connecting the chess AI engine
to the Lichess API for playing games online.

Usage:
  python run_lichess_bot.py [--difficulty=3] [--time-limit=5]
"""

import os
import sys
import argparse
import logging
import signal
import time
from typing import Optional

# Import modules directly from their filesystem path
import os.path
import sys

# Get the absolute path of the script directory
script_dir = os.path.dirname(os.path.abspath(__file__))

# Import directly from local files
sys.path.insert(0, script_dir)

# Now import our modules
from chess_ai.bot_runner import LichessBotRunner 
from chess_ai.lichess_bot import logger as lich

# Debug imports
print(f"Importing from: {script_dir}")
print(f"LichessBotRunner methods: {[method for method in dir(LichessBotRunner) if not method.startswith('_')]}")

# Global variable to hold the bot runner for signal handling
bot_runner = None


def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Lichess Chess Bot Runner")
    
    parser.add_argument(
        "--difficulty", 
        type=int, 
        choices=range(1, 6),
        default=3, 
        help="AI difficulty level (1-5, default: 3)"
    )
    
    parser.add_argument(
        "--time-limit", 
        type=float, 
        default=5.0, 
        help="Time limit for move calculation in seconds (default: 5.0)"
    )
    
    parser.add_argument(
        "--verbose", 
        action="store_true", 
        help="Enable verbose logging"
    )
    
    return parser.parse_args()


def signal_handler(sig, frame):
    """Handle termination signals for graceful shutdown."""
    global bot_runner
    
    if sig == signal.SIGINT:
        lich.info("Received keyboard interrupt (CTRL+C)")
    elif sig == signal.SIGTERM:
        lich.info("Received termination signal")
    
    lich.info("Initiating graceful shutdown...")
    
    if bot_runner is not None:
        bot_runner.cleanup()
    
    lich.info("Bot shutdown complete. Exiting.")
    sys.exit(0)


def setup_logging(verbose=False):
    """Configure logging."""
    # Already setup in lichess_bot.py, just adjust console level if verbose
    if verbose:
        console_handler = None
        for handler in lich.handlers:
            if isinstance(handler, logging.StreamHandler) and handler.stream == sys.stdout:
                console_handler = handler
                break
                
        if console_handler:
            console_handler.setLevel(logging.DEBUG)
            lich.info("Verbose logging enabled")


def main():
    """Main entry point for the Lichess bot."""
    global bot_runner
    
    # Parse command-line arguments
    args = parse_arguments()
    
    # Setup logging
    setup_logging(args.verbose)
    
    # Register signal handlers for graceful shutdown
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        # Print startup banner
        print("="*50)
        print(f"Starting Lichess Chess Bot (Difficulty: {args.difficulty})")
        print(f"Time limit per move: {args.time_limit} seconds")
        print("Press Ctrl+C to exit")
        print("="*50)
        
        # Create and initialize the bot runner
        lich.info(f"Initializing bot with difficulty {args.difficulty} and time limit {args.time_limit}s")
        bot_runner = LichessBotRunner(difficulty=args.difficulty)
        
        # Set time limit for the AI engine
        bot_runner.ai_engine.set_time_limit(args.time_limit)
        
        # Run the bot (this will block until the bot is stopped)
        bot_runner.run()
        
    except KeyboardInterrupt:
        # This should be caught by the signal handler
        pass
    except Exception as e:
        lich.error(f"Unhandled exception: {e}", exc_info=True)
        if bot_runner is not None:
            bot_runner.cleanup()
        sys.exit(1)


if __name__ == "__main__":
    main()

