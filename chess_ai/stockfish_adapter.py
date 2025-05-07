"""
Stockfish adapter for Eve's Chess AI.

This module integrates the Stockfish chess engine with personality-based
move selection to create a more human-like playing experience with
varying skill levels.
"""

import os
import random
import time
import json
import logging
from typing import Dict, List, Optional, Tuple, Any, Union
from pathlib import Path
import chess
import chess.engine
import chess.pgn
from stockfish import Stockfish

# Configure logging
logger = logging.getLogger(__name__)


class StockfishAdapter:
    """
    Adapter for Stockfish chess engine with personality-based move selection.
    
    This class manages the Stockfish engine and adds human-like behavior,
    varying skill levels, opening book knowledge, and personality traits
    to make Eve's chess play more engaging and natural.
    """
    
    # Mapping of personality traits to numerical effects
    PERSONALITY_TRAITS = {
        'aggressive': {
            'description': 'Prefers attacking moves and sacrifices',
            'tactical_bonus': 0.2,     # Bonus for tactical/attacking moves
            'material_value': -0.1,    # Cares less about material
            'pawn_advancement': 0.15,  # Likes advancing pawns
            'piece_activity': 0.15,    # Values active pieces over passive ones
        },
        'defensive': {
            'description': 'Prefers solid positions and safety',
            'tactical_bonus': -0.1,    # Less interested in tactics
            'material_value': 0.1,     # Values material more
            'pawn_advancement': -0.1,  # More cautious with pawn structure
            'piece_activity': 0.0,     # Neutral on piece activity
        },
        'creative': {
            'description': 'Plays unusual and surprising moves',
            'tactical_bonus': 0.1,     # Some preference for tactics
            'material_value': -0.1,    # Less concerned with material
            'pawn_advancement': 0.0,   # Neutral on pawn advancement
            'piece_activity': 0.2,     # Strongly prefers active pieces
        },
        'solid': {
            'description': 'Plays principled, theoretically sound moves',
            'tactical_bonus': 0.0,     # Neutral on tactics
            'material_value': 0.0,     # Balanced view of material
            'pawn_advancement': 0.0,   # Neutral on pawn advancement
            'piece_activity': 0.0,     # Neutral on piece activity
        },
        'positional': {
            'description': 'Focuses on long-term positional advantages',
            'tactical_bonus': -0.1,    # Less interested in immediate tactics
            'material_value': -0.05,   # Slightly less concerned with material
            'pawn_advancement': 0.05,  # Moderately values pawn structure
            'piece_activity': 0.1,     # Values piece coordination
        }
    }
    
    # Personality-based opening repertoire mapping
    PERSONALITY_OPENINGS = {
        'aggressive': [
            'King\'s Gambit', 'Vienna Gambit', 'Sicilian Dragon', 'Alekhine Defense',
            'Benko Gambit', 'Evans Gambit', 'Scotch Gambit'
        ],
        'defensive': [
            'Caro-Kann', 'French Defense', 'Berlin Defense', 'Queen\'s Gambit Declined', 
            'Slav Defense', 'Petroff Defense'
        ],
        'creative': [
            'Sicilian Najdorf', 'King\'s Indian', 'Modern Defense', 'Nimzo-Indian',
            'Alekhine Defense', 'Budapest Gambit'
        ],
        'solid': [
            'Queen\'s Gambit', 'Ruy Lopez', 'Italian Game', 'London System',
            'Semi-Slav', 'Caro-Kann'
        ],
        'positional': [
            'Catalan Opening', 'English Opening', 'Reti Opening', 'Queen\'s Indian Defense',
            'Nimzo-Indian', 'Closed Sicilian'
        ]
    }

    # Eve's preferred openings (key=opening name, value=list of moves in UCI format)
    OPENING_REPERTOIRE = {
        # --- WHITE OPENINGS ---
        
        # d4 openings (Queen's pawn)
        'Queen\'s Gambit': ['d2d4', 'd7d5', 'c2c4'],           # 1.d4 d5 2.c4
        'Queen\'s Gambit Accepted': ['d2d4', 'd7d5', 'c2c4', 'd5c4'],  # 1.d4 d5 2.c4 dxc4
        'Queen\'s Gambit Declined': ['d2d4', 'd7d5', 'c2c4', 'e7e6'],  # 1.d4 d5 2.c4 e6
        'Slav Defense': ['d2d4', 'd7d5', 'c2c4', 'c7c6'],       # 1.d4 d5 2.c4 c6
        'Semi-Slav': ['d2d4', 'd7d5', 'c2c4', 'c7c6', 'g1f3', 'e7e6'],  # 1.d4 d5 2.c4 c6 3.Nf3 e6
        'London System': ['d2d4', 'g1f3', 'c1f4'],              # 1.d4 Nf3 2.Bf4
        'Catalan Opening': ['d2d4', 'g1f3', 'c2c4', 'g2g3'],    # 1.d4 Nf3 2.c4 g3
        
        # e4 openings (King's pawn)
        'Italian Game': ['e2e4', 'e7e5', 'g1f3', 'b8c6', 'f1c4'],  # 1.e4 e5 2.Nf3 Nc6 3.Bc4
        'Evans Gambit': ['e2e4', 'e7e5', 'g1f3', 'b8c6', 'f1c4', 'f8c5', 'b2b4'],  # 1.e4 e5 2.Nf3 Nc6 3.Bc4 Bc5 4.b4
        'Ruy Lopez': ['e2e4', 'e7e5', 'g1f3', 'b8c6', 'f1b5'],  # 1.e4 e5 2.Nf3 Nc6 3.Bb5
        'Berlin Defense': ['e2e4', 'e7e5', 'g1f3', 'g8f6'],     # 1.e4 e5 2.Nf3 Nf6
        'Scotch Game': ['e2e4', 'e7e5', 'g1f3', 'b8c6', 'd2d4'],  # 1.e4 e5 2.Nf3 Nc6 3.d4
        'Scotch Gambit': ['e2e4', 'e7e5', 'g1f3', 'b8c6', 'd2d4', 'e5d4', 'f1c4'],  # 1.e4 e5 2.Nf3 Nc6 3.d4 exd4 4.Bc4
        'Vienna Game': ['e2e4', 'e7e5', 'b1c3'],               # 1.e4 e5 2.Nc3
        'Vienna Gambit': ['e2e4', 'e7e5', 'b1c3', 'g8f6', 'f2f4'],  # 1.e4 e5 2.Nc3 Nf6 3.f4
        'King\'s Gambit': ['e2e4', 'e7e5', 'f2f4'],            # 1.e4 e5 2.f4
        'Closed Sicilian': ['e2e4', 'c7c5', 'b1c3', 'b8c6', 'g2g3'],  # 1.e4 c5 2.Nc3 Nc6 3.g3
        
        # Flank openings
        'English Opening': ['c2c4', 'e7e5', 'b1c3'],           # 1.c4 e5 2.Nc3
        'Reti Opening': ['g1f3', 'd7d5', 'c2c4'],              # 1.Nf3 d5 2.c4
        
        # --- BLACK OPENINGS ---
        
        # Against e4
        'Sicilian Defense': ['e2e4', 'c7c5'],                  # 1.e4 c5
        'Sicilian Dragon': ['e2e4', 'c7c5', 'g1f3', 'd7d6', 'd2d4', 'c5d4', 'f3d4', 'g8f6', 'b1c3', 'g7g6'],  # Dragon variation
        'Sicilian Najdorf': ['e2e4', 'c7c5', 'g1f3', 'd7d6', 'd2d4', 'c5d4', 'f3d4', 'g8f6', 'b1c3', 'a7a6'],  # Najdorf variation
        'French Defense': ['e2e4', 'e7e6', 'd2d4', 'd7d5'],    # 1.e4 e6 2.d4 d5
        'Caro-Kann': ['e2e4', 'c7c6'],                         # 1.e4 c6
        'Alekhine Defense': ['e2e4', 'g8f6'],                  # 1.e4 Nf6
        'Modern Defense': ['e2e4', 'g7g6'],                    # 1.e4 g6
        'Petroff Defense': ['e2e4', 'e7e5', 'g1f3', 'g8f6'],   # 1.e4 e5 2.Nf3 Nf6
        
        # Against d4
        'Queen\'s Indian Defense': ['d2d4', 'g8f6', 'c2c4', 'e7e6', 'g1f3', 'b7b6'],  # 1.d4 Nf6 2.c4 e6 3.Nf3 b6
        'King\'s Indian': ['d2d4', 'g8f6', 'c2c4', 'g7g6', 'b1c3', 'f8g7', 'e2e4', 'd7d6'],  # 1.d4 Nf6 2.c4 g6 3.Nc3 Bg7 4.e4 d6
        'Nimzo-Indian': ['d2d4', 'g8f6', 'c2c4', 'e7e6', 'b1c3', 'f8b4'],  # 1.d4 Nf6 2.c4 e6 3.Nc3 Bb4
        'Benko Gambit': ['d2d4', 'g8f6', 'c2c4', 'c7c5', 'd4d5', 'b7b5'],  # 1.d4 Nf6 2.c4 c5 3.d5 b5
        'Budapest Gambit': ['d2d4', 'g8f6', 'c2c4', 'e7e5'],   # 1.d4 Nf6 2.c4 e5
    }
    
    # Skill level ranges by ELO
    SKILL_RANGES = {
        'beginner': (0, 10),   # ~800 ELO
        'intermediate': (10, 15),  # ~1500 ELO
        'advanced': (15, 18),  # ~1800 ELO
        'expert': (18, 20),    # ~2500+ ELO
    }
    
    def __init__(
        self, 
        stockfish_path: Optional[str] = None,
        personality: str = 'solid',
        default_rating: int = 1500,
        opening_book_path: Optional[str] = None
    ):
        """
        Initialize the Stockfish adapter with personality traits.
        
        Args:
            stockfish_path: Path to Stockfish executable (uses PATH if None)
            personality: Personality trait name from PERSONALITY_TRAITS
            default_rating: Initial ELO rating for the engine
            opening_book_path: Path to opening book JSON file
        """
        # Try to find Stockfish executable if not specified
        if stockfish_path is None:
            # Default paths to look for Stockfish
            default_paths = [
                # macOS Homebrew installation
                "/opt/homebrew/bin/stockfish",
                # Linux common paths
                "/usr/bin/stockfish",
                "/usr/local/bin/stockfish",
                # Windows (assuming it's in PATH)
                "stockfish.exe"
            ]
            
            for path in default_paths:
                if os.path.exists(path):
                    stockfish_path = path
                    break
        
        # Initialize engine
        try:
            self.stockfish = Stockfish(path=stockfish_path)
            
            # Get version info - handle different method names in different stockfish package versions
            try:
                if hasattr(self.stockfish, 'get_stockfish_major_version'):
                    version = self.stockfish.get_stockfish_major_version()
                    logger.info(f"Stockfish engine initialized with major version: {version}")
                elif hasattr(self.stockfish, 'get_stockfish_version'):
                    version = self.stockfish.get_stockfish_version()
                    logger.info(f"Stockfish engine initialized with version: {version}")
                else:
                    # If no version method is available, just log that it's initialized
                    logger.info("Stockfish engine initialized successfully (version unknown)")
            except Exception as version_error:
                # Version check failed but engine may still work
                logger.warning(f"Could not determine Stockfish version: {version_error}")
                
        except Exception as e:
            logger.error(f"Error initializing Stockfish: {e}")
            raise ValueError(f"Could not initialize Stockfish: {e}")
        
        # Set personality traits
        self.set_personality(personality)
        
        # Set default ELO rating
        self.set_elo_rating(default_rating)
        
        # Initialize opening book
        self.opening_book = {}
        self.opening_book_path = opening_book_path
        if opening_book_path and os.path.exists(opening_book_path):
            self._load_opening_book(opening_book_path)
        else:
            # Use built-in repertoire
            self.opening_book = self.OPENING_REPERTOIRE
        
        # Track whether we're in an opening
        self.current_opening = None
        self.current_position_fen = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
        self.move_history = []
        
    def set_personality(self, personality: str) -> None:
        """
        Set Eve's chess personality traits.
        
        Args:
            personality: Name of the personality from PERSONALITY_TRAITS
        """
        if personality not in self.PERSONALITY_TRAITS:
            valid_personalities = ", ".join(self.PERSONALITY_TRAITS.keys())
            logger.warning(f"Unknown personality '{personality}'. Valid options: {valid_personalities}")
            personality = 'solid'  # Default to solid if personality is unknown
            
        self.personality = personality
        self.traits = self.PERSONALITY_TRAITS[personality]
        logger.info(f"Set chess personality to '{personality}': {self.traits['description']}")
        
    def set_elo_rating(self, elo: int) -> None:
        """
        Set the engine's approximate ELO rating.
        
        Args:
            elo: Target ELO rating (800-3000)
        """
        self.target_elo = max(800, min(3000, elo))  # Clamp between 800-3000
        
        # Determine skill level based on ELO
        if elo <= 1000:
            skill_range = self.SKILL_RANGES['beginner']
            # Also reduce depth for very low ratings
            self.stockfish.set_depth(2)
            self.make_blunders = True
            self.blunder_probability = 0.25  # 25% chance of blunders
        elif elo <= 1600:
            skill_range = self.SKILL_RANGES['intermediate']
            self.stockfish.set_depth(10)
            self.make_blunders = True
            self.blunder_probability = 0.1  # 10% chance of blunders
        elif elo <= 2000:
            skill_range = self.SKILL_RANGES['advanced']
            self.stockfish.set_depth(14)
            self.make_blunders = True
            self.blunder_probability = 0.05  # 5% chance of blunders
        else:
            skill_range = self.SKILL_RANGES['expert']
            self.stockfish.set_depth(18)
            self.make_blunders = False
            self.blunder_probability = 0.0
            
        # Randomize skill within the appropriate range
        skill_min, skill_max = skill_range
        skill_level = random.randint(skill_min, skill_max)
        
        # Set engine parameters
        self.stockfish.set_skill_level(skill_level)
        self.stockfish.set_elo_rating(self.target_elo)
        
        logger.info(f"Set ELO rating to {self.target_elo}, skill level {skill_level}")
        
    def _load_opening_book(self, book_path: str) -> None:
        """
        Load opening book from a JSON file.
        
        Args:
            book_path: Path to opening book JSON file
        """
        try:
            with open(book_path, 'r') as f:
                loaded_book = json.load(f)
                
            # Validate and convert moves to proper UCI format if needed
            validated_book = {}
            for opening_name, moves in loaded_book.items():
                validated_moves = []
                valid_opening = True
                
                for move in moves:
                    # If the move is in short algebraic notation (e.g., "e4"), 
                    # try to convert it to UCI format (e.g., "e2e4")
                    if len(move) < 4:
                        logger.warning(f"Skipping opening {opening_name} due to short move notation: {move}")
                        valid_opening = False
                        break
                    
                    # Validate the move
                    try:
                        # This will throw an exception if the move is not valid UCI
                        _ = chess.Move.from_uci(move)
                        validated_moves.append(move)
                    except Exception:
                        logger.warning(f"Invalid move in opening {opening_name}: {move}")
                        valid_opening = False
                        break
                
                if valid_opening:
                    validated_book[opening_name] = validated_moves
            
            self.opening_book = validated_book
            logger.info(f"Loaded opening book from {book_path} with {len(self.opening_book)} openings")
        except Exception as e:
            logger.error(f"Error loading opening book: {e}")
            # Fall back to built-in repertoire
            self.opening_book = self.OPENING_REPERTOIRE
            
    def set_position(self, fen: str, moves: List[str] = None) -> None:
        """
        Set the current position for analysis.
        
        Args:
            fen: FEN string representation of the position
            moves: List of moves made after the position in UCI format
        """
        self.current_position_fen = fen
        self.move_history = moves or []
        
        # Update Stockfish with the position
        try:
            self.stockfish.set_position(self.move_history)
            logger.debug(f"Position set to: {fen}")
        except Exception as e:
            logger.error(f"Error setting position: {e}")
            
    def get_best_move(self) -> str:
        """
        Get the best move according to Stockfish.
        
        Returns:
            Best move in UCI format (e.g., "e2e4")
        """
        try:
            return self.stockfish.get_best_move()
        except Exception as e:
            logger.error(f"Error getting best move: {e}")
            # If Stockfish fails, return a random legal move
            board = chess.Board(self.current_position_fen)
            for move in self.move_history:
                board.push_uci(move)
            legal_moves = list(board.legal_moves)
            if legal_moves:
                return legal_moves[random.randint(0, len(legal_moves) - 1)].uci()
            return None
            
    def get_top_moves(self, num_moves: int = 3) -> List[Dict[str, Any]]:
        """
        Get the top N moves with scores.
        
        Args:
            num_moves: Number of top moves to return
            
        Returns:
            List of dicts containing {'Move': move, 'Centipawn': score, 'Mate': mate_in_n}
        """
        try:
            return self.stockfish.get_top_moves(num_moves)
        except Exception as e:
            logger.error(f"Error getting top moves: {e}")
            return []
            
    def _check_opening_book(self, position: chess.Board) -> Optional[str]:
        """
        Check if the current position matches an opening in the repertoire.
        
        Args:
            position: Chess board position
            
        Returns:
            Move from opening book or None if not found
        """
        # Filter openings by personality preference if possible
        preferred_openings = self.PERSONALITY_OPENINGS.get(self.personality, [])
        
        # Check for personality-preferred openings first
        personality_matches = []
        other_matches = []
        
        # If we have a sequence of moves
        if self.move_history:
            # Convert move history to a move sequence for lookup
            move_sequence = ' '.join(self.move_history)
            
            # Check each opening
            for opening_name, moves in self.opening_book.items():
                # Skip if we don't have enough moves to match
                if len(moves) <= len(self.move_history):
                    continue
                    
                # Ensure all moves are in UCI format (from, to squares)
                validated_moves = []
                valid_sequence = True
                
                for i, move_str in enumerate(moves[:len(self.move_history)]):
                    # Check if the move is in proper UCI format (e.g., "e2e4")
                    if len(move_str) < 4:
                        logger.warning(f"Invalid move format in opening {opening_name}: {move_str}")
                        valid_sequence = False
                        break
                    validated_moves.append(move_str)
                    
                if not valid_sequence or len(validated_moves) != len(self.move_history):
                    continue
                    
                opening_str = ' '.join(validated_moves)
                
                # If our move history matches the start of this opening
                if opening_str == move_sequence:
                    # Get the next move and ensure it's in UCI format
                    next_move = moves[len(self.move_history)]
                    
                    # Validate the move format
                    if len(next_move) < 4:
                        logger.warning(f"Invalid next move format in {opening_name}: {next_move}")
                        continue
                        
                    try:
                        # Verify it's a valid UCI move
                        move_obj = chess.Move.from_uci(next_move)
                        
                        # Verify the move is legal in the current position
                        if move_obj in position.legal_moves:
                            # Sort into personality preferred or other matches
                            if opening_name in preferred_openings:
                                personality_matches.append((opening_name, next_move))
                            else:
                                other_matches.append((opening_name, next_move))
                        else:
                            logger.warning(f"Opening book move {next_move} not legal in current position")
                    except Exception as e:
                        logger.warning(f"Invalid next move in {opening_name}: {next_move} - {e}")
        
        # Special case: if we're at the beginning, suggest first moves
        elif not self.move_history:
            # Starting position - get first moves from our openings
            for opening_name, moves in self.opening_book.items():
                if not moves:
                    continue
                    
                # Get first move
                first_move = moves[0]
                
                # Validate move format and legality
                if len(first_move) >= 4:
                    try:
                        move_obj = chess.Move.from_uci(first_move)
                        if move_obj in position.legal_moves:
                            if opening_name in preferred_openings:
                                personality_matches.append((opening_name, first_move))
                            else:
                                other_matches.append((opening_name, first_move))
                    except Exception as e:
                        logger.warning(f"Invalid first move in {opening_name}: {first_move} - {e}")
        
        # Choose from personality matches first if available, otherwise fallback to other matches
        matching_openings = personality_matches if personality_matches else other_matches
        
        if matching_openings:
            # Personality preference: higher chance of selecting a preferred opening
            if personality_matches and random.random() < 0.8:  # 80% chance to pick from preferred
                opening_name, next_move = random.choice(personality_matches)
                logger.info(f"Using personality-preferred opening: {opening_name}")
            else:
                opening_name, next_move = random.choice(matching_openings)
                
            self.current_opening = opening_name
            logger.info(f"Using opening book move from {opening_name}: {next_move}")
            return next_move
            
        return None
        
    def _introduce_blunder(self, top_moves: List[Dict[str, Any]]) -> str:
        """
        Deliberately introduces a mistake based on skill level.
        
        Args:
            top_moves: List of top moves from Stockfish
            
        Returns:
            Move string that may be suboptimal
        """
        if not top_moves:
            return self.get_best_move()
            
        best_move = top_moves[0]['Move']
        
        # If we shouldn't blunder, return the best move
        if not self.make_blunders or random.random() > self.blunder_probability:
            return best_move
            
        # Create a chess board from current position
        board = chess.Board(self.current_position_fen)
        for move in self.move_history:
            board.push_uci(move)
            
        # Get all legal moves
        legal_moves = list(board.legal_moves)
        if len(legal_moves) <= 1:
            return best_move  # Only one legal move
            
        # Filter out the top N moves to find suboptimal ones
        top_move_strs = [move['Move'] for move in top_moves]
        
        # Choose a blunder strategy based on rating
        if self.target_elo <= 1000:
            # Beginners might make obvious blunders
            # Get a random legal move (could be terrible)
            blunder = legal_moves[random.randint(0, len(legal_moves) - 1)].uci()
        elif self.target_elo <= 1600:
            # Intermediate players make positional or tactical errors
            # Get a move that's not in the top 3
            if len(legal_moves) > 3:
                possible_blunders = [move.uci() for move in legal_moves 
                                   if move.uci() not in top_move_strs[:3]]
                if possible_blunders:
                    blunder = random.choice(possible_blunders)
                else:
                    # Fall back to second-best move if we can't find a clear blunder
                    blunder = top_moves[1]['Move'] if len(top_moves) > 1 else best_move
            else:
                # Not enough moves to choose from, pick second best
                blunder = top_moves[1]['Move'] if len(top_moves) > 1 else best_move
        else:
            # Advanced players make subtle errors
            # Choose the second or third best move
            if len(top_moves) > 2:
                # Small mistake - take second or third best move
                blunder_idx = random.randint(1, min(2, len(top_moves) - 1))
                blunder = top_moves[blunder_idx]['Move']
            else:
                # Not enough options, take second best if available
                blunder = top_moves[1]['Move'] if len(top_moves) > 1 else best_move
                
        logger.debug(f"Introducing blunder: {blunder} instead of {best_move}")
        return blunder
        
    def _apply_personality_to_moves(self, top_moves: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Adjust move evaluations based on personality traits.
        
        Args:
            top_moves: List of top moves from Stockfish
            
        Returns:
            Best move after personality adjustment
        """
        if not top_moves:
            return self.get_best_move()
            
        # Create a chess board from current position
        board = chess.Board(self.current_position_fen)
        for move in self.move_history:
            board.push_uci(move)
            
        # Create copies with personality-adjusted scores
        adjusted_moves = []
        
        for move_info in top_moves:
            move_uci = move_info['Move']
            score = move_info.get('Centipawn', 0) or 0  # Handle None
            
            # Parse the move
            move = chess.Move.from_uci(move_uci)
            
            # Apply personality adjustments
            adjusted_score = score
            
            # Check if move is a capture
            is_capture = board.is_capture(move)
            if is_capture:
                # Adjust based on material value trait
                adjusted_score += 50 * self.traits['material_value']
                
            # Check if move is a check
            board_copy = board.copy()
            board_copy.push(move)
            is_check = board_copy.is_check()
            if is_check:
                # Tactical moves are favored by aggressive personalities
                adjusted_score += 40 * self.traits['tactical_bonus']
                
            # Check if move advances a pawn
            from_square = move.from_square
            piece = board.piece_at(from_square)
            if piece and piece.piece_type == chess.PAWN:
                rank_diff = chess.square_rank(move.to_square) - chess.square_rank(from_square)
                # Positive for white moving up, negative for black moving down
                pawn_advancement = rank_diff if piece.color == chess.WHITE else -rank_diff
                if pawn_advancement > 0:
                    adjusted_score += 30 * self.traits['pawn_advancement']
                    
            # Check for piece activity (center control)
            to_square = move.to_square
            to_file, to_rank = chess.square_file(to_square), chess.square_rank(to_square)
            
            # Center squares have higher activity value
            center_value = 0
            if 2 <= to_file <= 5 and 2 <= to_rank <= 5:
                center_value = 20
                if 3 <= to_file <= 4 and 3 <= to_rank <= 4:
                    center_value = 40  # Central 4 squares
                    
            adjusted_score += center_value * self.traits['piece_activity']
            
            # Add adjusted move to list
            adjusted_moves.append({
                'Move': move_uci,
                'OriginalScore': score,
                'AdjustedScore': adjusted_score,
                'Mate': move_info.get('Mate')
            })
            
        # Sort by adjusted score
        adjusted_moves.sort(key=lambda x: x['AdjustedScore'], reverse=True)
        
        # Return the best move after personality adjustment
        if adjusted_moves:
            logger.debug(f"Personality adjusted move: {adjusted_moves[0]['Move']} " +
                       f"(Original: {top_moves[0]['Move']})")
            return adjusted_moves[0]['Move']
        
        return top_moves[0]['Move']
        
    def _maybe_play_brilliancy(self, rating_threshold: int = 2200) -> Optional[str]:
        """
        Occasionally play a brilliant move above current rating to simulate flash of insight.
        
        Args:
            rating_threshold: Minimum rating for moves considered brilliant
            
        Returns:
            Brilliant move or None if no brilliancy is played
        """
        # Only 5% chance of brilliancy
        if random.random() > 0.05:
            return None
            
        # Get current settings
        try:
            # Store current parameters - try different ways to access them
            # based on stockfish library version
            current_depth = None
            current_skill = None
            
            # Set to expert level
            self.stockfish.set_depth(20)
            self.stockfish.set_skill_level(20)
            
            # Get best expert move
            brilliant_move = self.stockfish.get_best_move()
            
            # Restore original settings if we had them
            if current_depth is not None:
                self.stockfish.set_depth(current_depth)
            if current_skill is not None:
                self.stockfish.set_skill_level(current_skill)
            else:
                # Just reset to our target ELO
                self.set_elo_rating(self.target_elo)
            
            if brilliant_move:
                # Validate move
                try:
                    board = chess.Board(self.current_position_fen)
                    for move in self.move_history:
                        board.push_uci(move)
                    
                    # Check if move is valid in this position
                    chess_move = chess.Move.from_uci(brilliant_move)
                    if chess_move in board.legal_moves:
                        logger.info(f"Playing a brilliant move: {brilliant_move}")
                        return brilliant_move
                    else:
                        logger.warning(f"Brilliant move {brilliant_move} not valid in current position")
                        return None
                except Exception as e:
                    logger.warning(f"Error validating brilliancy: {e}")
                    return None
            
            return None
        except Exception as e:
            logger.warning(f"Error generating brilliancy: {e}")
            return None
            
    def get_move(self, fen: str = None, moves: List[str] = None) -> Dict[str, Any]:
        """
        Get Eve's move based on personality, rating, and opening knowledge.
        
        This is the main method that combines all features to produce
        a human-like move with appropriate commentary.
        
        Args:
            fen: Optional FEN string (if different from current position)
            moves: Optional move history (if different from current)
            
        Returns:
            Dict with move data including:
            - 'move': Selected move in UCI format
            - 'commentary': Eve's commentary on the move
            - 'evaluation': Position evaluation 
            - 'opening': Opening name if applicable
            - 'confidence': How confident Eve is in this move
            - 'thinking_time': Simulated thinking time
            - 'move_type': Type of move (book, normal, blunder, brilliant)
        """
        # Update position if provided
        if fen:
            self.set_position(fen, moves)
            
        # Track start time
        start_time = time.time()
        
        # Create a chess board from current position for analysis
        board = chess.Board(self.current_position_fen)
        for move in self.move_history:
            try:
                board.push_uci(move)
            except Exception as e:
                logger.error(f"Error applying move {move} to board: {e}")
                # Try to recover by creating a fresh board
                board = chess.Board(self.current_position_fen)
                break
            
        # First, check opening book for known moves
        book_move = self._check_opening_book(board)
        opening_name = self.current_opening
        
        # Check for brilliant move opportunity (rare)
        brilliant_move = self._maybe_play_brilliancy()
        
        # Get top engine moves
        try:
            top_moves = self.get_top_moves(5)  # Get top 5 moves for more variety
        except Exception as e:
            logger.error(f"Error getting top moves: {e}")
            top_moves = []
        
        selected_move = None
        move_type = "normal"  # Default type
        confidence = 0.8  # Default confidence
        
        # Decide which move to play
        try:
            if book_move:
                # Verify the book move is valid in this position
                try:
                    move_obj = chess.Move.from_uci(book_move)
                    if move_obj in board.legal_moves:
                        selected_move = book_move
                        confidence = 0.9  # High confidence in book moves
                        move_type = "book"
                    else:
                        logger.warning(f"Opening book move {book_move} not legal, using engine move instead")
                except Exception as e:
                    logger.warning(f"Error validating book move: {e}")
            
            # Use brilliant move if available and not using opening book
            if not selected_move and brilliant_move:
                try:
                    move_obj = chess.Move.from_uci(brilliant_move)
                    if move_obj in board.legal_moves:
                        selected_move = brilliant_move
                        confidence = 0.95  # Very high confidence in brilliant moves
                        move_type = "brilliant"
                    else:
                        logger.warning(f"Brilliant move {brilliant_move} not legal, using engine move instead")
                except Exception as e:
                    logger.warning(f"Error validating brilliant move: {e}")
            
            # If not using book or brilliancy, use normal engine move selection
            if not selected_move:
                if top_moves:
                    # Apply personality to adjust move preferences
                    personality_move = self._apply_personality_to_moves(top_moves)
                    
                    # Maybe introduce a blunder based on rating
                    if self.make_blunders and random.random() < self.blunder_probability:
                        blunder_move = self._introduce_blunder(top_moves)
                        # Verify blunder is legal
                        try:
                            move_obj = chess.Move.from_uci(blunder_move)
                            if move_obj in board.legal_moves:
                                selected_move = blunder_move
                                confidence = 0.4 + random.random() * 0.4  # Lower confidence (0.4-0.8)
                                move_type = "blunder"
                            else:
                                # Fallback to personality move
                                selected_move = personality_move
                                confidence = 0.7 + random.random() * 0.2  # Normal confidence (0.7-0.9)
                                move_type = "normal"
                        except Exception as e:
                            logger.warning(f"Error validating blunder move: {e}")
                            selected_move = personality_move
                            move_type = "normal"
                    else:
                        # Use personality-adjusted move
                        selected_move = personality_move
                        confidence = 0.7 + random.random() * 0.2  # Normal confidence (0.7-0.9)
                        move_type = "normal"
                else:
                    # No top moves available, get best move directly
                    best_move = self.get_best_move()
                    if best_move:
                        selected_move = best_move
                        confidence = 0.6  # Medium confidence
                        move_type = "direct"
        except Exception as e:
            logger.error(f"Error selecting move: {e}")

        # If all above methods failed, try to get any legal move
        if not selected_move:
            # Last resort: Get a random legal move
            try:
                legal_moves = list(board.legal_moves)
                if legal_moves:
                    selected_move = random.choice(legal_moves).uci()
                    confidence = 0.3  # Low confidence (fallback option)
                    move_type = "fallback"
                else:
                    # No legal moves available (shouldn't happen in normal chess)
                    logger.error("No legal moves available in position")
                    # Return a placeholder response
                    return {
                        'move': None,
                        'commentary': "I don't see any legal moves in this position!",
                        'evaluation': None,
                        'opening': None,
                        'confidence': 0.0,
                        'thinking_time': time.time() - start_time,
                        'move_type': "none"
                    }
            except Exception as e:
                logger.error(f"Critical error getting any legal move: {e}")
                # Return a placeholder response
                return {
                    'move': None,
                    'commentary': "I'm having trouble analyzing this position.",
                    'evaluation': None,
                    'opening': None,
                    'confidence': 0.0,
                    'thinking_time': time.time() - start_time,
                    'move_type': "error"
                }
        
        # Generate commentary for the move
        try:
            commentary = self.generate_move_commentary(selected_move, board, move_type, confidence)
        except Exception as e:
            logger.error(f"Error generating commentary: {e}")
            # Fallback commentary
            piece_names = {
                'p': 'pawn', 'n': 'knight', 'b': 'bishop', 
                'r': 'rook', 'q': 'queen', 'k': 'king'
            }
            try:
                # Try to get basic piece info
                move_obj = chess.Move.from_uci(selected_move)
                from_square = chess.square_name(move_obj.from_square)
                to_square = chess.square_name(move_obj.to_square)
                piece = board.piece_at(move_obj.from_square)
                if piece:
                    piece_name = piece_names.get(piece.symbol().lower(), 'piece')
                    commentary = f"I'll move my {piece_name} from {from_square} to {to_square}."
                else:
                    commentary = f"I'll play {selected_move}."
            except:
                commentary = "Here's my move."
        
        # Calculate a realistic thinking time based on position complexity and rating
        # Higher rated players think faster, except for complex positions
        complexity = min(len(top_moves) if top_moves else 1, 3) * 0.5
        base_time = 2.0  # Base thinking time in seconds
        skill_time_reduction = (self.target_elo - 800) / 2000  # 0-0.6 time reduction for skill
        
        thinking_time = max(0.8, base_time + complexity - skill_time_reduction)
        
        # Ensure minimum time elapsed
        elapsed = time.time() - start_time
        if elapsed < thinking_time:
            time.sleep(thinking_time - elapsed)
        
        # Get evaluation after move
        try:
            evaluation = self.evaluate_position_after_move(selected_move, board)
        except Exception as e:
            logger.error(f"Error evaluating position: {e}")
            evaluation = {
                'score': 0,
                'mate': None,
                'description': "The position seems balanced."
            }
        
        # Return complete move data
        return {
            'move': selected_move,
            'commentary': commentary,
            'evaluation': evaluation,
            'opening': opening_name,
            'confidence': confidence,
            'thinking_time': time.time() - start_time,
            'move_type': move_type
        }
        
    def generate_move_commentary(self, move: str, board: chess.Board, 
                               move_type: str, confidence: float) -> str:
        """
        Generate Eve's commentary on a move based on her personality.
        
        Args:
            move: The selected move in UCI format
            board: Current chess board position
            move_type: Type of move (book, normal, blunder, brilliant)
            confidence: Confidence level in the move (0-1)
            
        Returns:
            Commentary string
        """
        # Parse the move
        chess_move = chess.Move.from_uci(move)
        
        # Basic move description
        from_square = chess.square_name(chess_move.from_square)
        to_square = chess.square_name(chess_move.to_square)
        piece = board.piece_at(chess_move.from_square)
        
        if not piece:
            return "I think this move is interesting."
            
        piece_name = chess.piece_name(piece.piece_type).capitalize()
        
        # Check move characteristics
        is_capture = board.is_capture(chess_move)
        board_copy = board.copy()
        board_copy.push(chess_move)
        gives_check = board_copy.is_check()
        
        # Build commentary based on personality and move type
        comments = []
        
        # Opening book moves
        if move_type == "book" and self.current_opening:
            opening_comments = [
                f"I'll play {from_square} to {to_square}, continuing with the {self.current_opening}.",
                f"This is a standard {self.current_opening} move.",
                f"In the {self.current_opening}, {piece_name} to {to_square} is a principled choice.",
                f"I know this position from the {self.current_opening}."
            ]
            return random.choice(opening_comments)
            
        # Brilliant moves
        if move_type == "brilliant":
            brilliant_comments = [
                f"Wait, I see something interesting! {piece_name} to {to_square}!",
                f"Oh! {from_square} to {to_square} looks really strong here!",
                f"I think {piece_name} to {to_square} is a winning move!",
                f"This might be surprising, but {piece_name} to {to_square} is very powerful!"
            ]
            return random.choice(brilliant_comments)
            
        # Capture descriptions
        if is_capture:
            capture_target = board.piece_at(chess_move.to_square)
            if capture_target:
                target_name = chess.piece_name(capture_target.piece_type).capitalize()
                
                if self.personality == 'aggressive':
                    comments.append(f"I'll capture the {target_name} with my {piece_name}.")
                    comments.append(f"Taking the {target_name} looks good here.")
                    comments.append(f"I think I should capture this {target_name}.")
                else:
                    comments.append(f"{piece_name} takes {target_name}.")
                    comments.append(f"I'll exchange my {piece_name} for the {target_name}.")
        
        # Check
        if gives_check:
            if self.personality == 'aggressive':
                comments.append("Check! Let's put some pressure on the king.")
                comments.append("I'll give a check and see how you respond.")
            else:
                comments.append("This check seems appropriate.")
                comments.append("Check. Let's see how you defend.")
        
        # Standard moves by personality
        if not comments:  # If no special commentary yet
            if self.personality == 'aggressive':
                comments.append(f"Moving my {piece_name} to {to_square} to increase the pressure.")
                comments.append(f"Let's advance the {piece_name} to {to_square}.")
                comments.append(f"{piece_name} to {to_square} looks attacking.")
            elif self.personality == 'defensive':
                comments.append(f"I'll move my {piece_name} to {to_square} for safety.")
                comments.append(f"Let's position the {piece_name} on {to_square} to strengthen my position.")
                comments.append(f"Moving {piece_name} to {to_square} gives me a solid structure.")
            elif self.personality == 'creative':
                comments.append(f"Let's try {piece_name} to {to_square}, which creates some interesting options.")
                comments.append(f"I think {piece_name} to {to_square} leads to an unusual position.")
                comments.append(f"This {piece_name} move to {to_square} might surprise you.")
            elif self.personality == 'solid':
                comments.append(f"Moving {piece_name} to {to_square} is principled.")
                comments.append(f"I'll develop my {piece_name} to {to_square}.")
                comments.append(f"{piece_name} to {to_square} follows good chess principles.")
            elif self.personality == 'positional':
                comments.append(f"I'll place my {piece_name} on {to_square} for long-term advantage.")
                comments.append(f"Moving {piece_name} to {to_square} improves my position.")
                comments.append(f"This {piece_name} maneuver to {to_square} gives me better coordination.")
                
        # Add confidence modifiers
        if confidence < 0.5:
            # Low confidence
            confidence_phrases = [
                "I'm not entirely sure, but ",
                "Perhaps ",
                "This might not be optimal, but ",
                "I'm considering "
            ]
            prefix = random.choice(confidence_phrases)
            if comments:
                comments[0] = prefix + comments[0][0].lower() + comments[0][1:]
        elif confidence > 0.9:
            # High confidence
            confidence_phrases = [
                "I'm confident that ",
                "This is clearly a good move: ",
                "The best move here is ",
                "Without a doubt, "
            ]
            prefix = random.choice(confidence_phrases)
            if comments:
                comments[0] = prefix + comments[0][0].lower() + comments[0][1:]
                
        # If no commentary was generated, use generic fallbacks
        if not comments:
            generic_comments = [
                f"I'll move my {piece_name} from {from_square} to {to_square}.",
                f"Let's play {piece_name} to {to_square}.",
                f"I think {from_square} to {to_square} is a reasonable move."
            ]
            comments = generic_comments
            
        # Select and return a random comment
        return random.choice(comments)
        
    def evaluate_position_after_move(self, move: str, board: chess.Board) -> Dict[str, Any]:
        """
        Evaluate the position after a potential move.
        
        Args:
            move: Move in UCI format
            board: Current chess board state
            
        Returns:
            Dictionary with evaluation data:
            - 'score': Centipawn score
            - 'mate': Mate in N moves (if applicable)
            - 'description': Text description of position
        """
        # Apply the move to a copied board
        board_copy = board.copy()
        chess_move = chess.Move.from_uci(move)
        board_copy.push(chess_move)
        
        # Set the position in Stockfish
        self.stockfish.set_fen_position(board_copy.fen())
        
        # Get evaluation
        try:
            evaluation = self.stockfish.get_evaluation()
            score = evaluation.get('value', 0)
            mate = evaluation.get('mate', None)
            
            # Generate a description based on evaluation
            description = self._generate_eval_description(score, mate)
            
            return {
                'score': score,
                'mate': mate,
                'description': description
            }
        except Exception as e:
            logger.error(f"Error evaluating position: {e}")
            return {
                'score': 0,
                'mate': None,
                'description': "The position is roughly equal."
            }
            
    def _generate_eval_description(self, score: int, mate: Optional[int]) -> str:
        """
        Generate a human-readable description of a position evaluation.
        
        Args:
            score: Centipawn score
            mate: Mate in N moves (or None)
            
        Returns:
            Human-readable description of the position
        """
        # Handle mate scores
        if mate is not None:
            if mate > 0:
                return f"I have a forced mate in {mate} moves."
            else:
                return f"I'm facing a forced mate in {abs(mate)} moves."
        
        # Handle regular scores
        # Adjust based on personality (positional players downplay material advantage)
        if self.personality == 'positional':
            score = int(score * 0.8)  # Reduce perceived advantage/disadvantage
            
        abs_score = abs(score)
        
        if abs_score < 50:
            return "The position is approximately equal."
        elif abs_score < 150:
            advantage = "slight advantage" if score > 0 else "slight disadvantage"
            return f"I have a {advantage}."
        elif abs_score < 350:
            advantage = "clear advantage" if score > 0 else "clear disadvantage"
            return f"I have a {advantage}."
        elif abs_score < 650:
            advantage = "winning advantage" if score > 0 else "losing position"
            return f"I have a {advantage}."
        else:
            if score > 0:
                return "I have a completely winning position."
            else:
                return "My position is very difficult."
    
    def cleanup(self) -> None:
        """
        Clean up resources used by the adapter.
        
        This should be called when the adapter is no longer needed
        to ensure all resources are properly released.
        """
        try:
            # Close Stockfish process if needed
            if hasattr(self, 'stockfish') and self.stockfish:
                # Different engines have different cleanup methods
                # python-stockfish doesn't explicitly require cleanup
                pass
            
            logger.info("StockfishAdapter resources released")
        except Exception as e:
            logger.error(f"Error during StockfishAdapter cleanup: {e}")
            
    def __del__(self) -> None:
        """Clean up resources when the adapter is deleted."""
        self.cleanup()
        
    def handle_error(self, error: Exception, fallback_move: Optional[str] = None) -> str:
        """
        Handle errors during move selection with graceful fallbacks.
        
        Args:
            error: The exception that occurred
            fallback_move: Optional fallback move if available
            
        Returns:
            A valid move or None if no move can be found
        """
        logger.error(f"Error in StockfishAdapter: {error}")
        
        if fallback_move:
            return fallback_move
            
        # Try to get a simple best move with minimal settings
        try:
            # Set minimal parameters to avoid complex calculations
            self.stockfish.set_depth(1)
            self.stockfish.set_skill_level(0)
            
            # Get a basic move
            basic_move = self.stockfish.get_best_move()
            
            # Restore original settings
            self.set_elo_rating(self.target_elo)
            
            return basic_move
        except Exception as nested_error:
            logger.error(f"Fallback error in StockfishAdapter: {nested_error}")
            
            # Last resort: try to find any legal move
            try:
                board = chess.Board(self.current_position_fen)
                for move in self.move_history:
                    board.push_uci(move)
                
                legal_moves = list(board.legal_moves)
                if legal_moves:
                    return random.choice(legal_moves).uci()
            except Exception as final_error:
                logger.error(f"Critical error in StockfishAdapter: {final_error}")
            
            return None

