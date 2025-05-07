"""
Chess position evaluation module.

This module provides functionality for evaluating chess positions,
including material counting, piece-square tables, and positional heuristics.
"""

from typing import Dict, List, Tuple, Optional

from .state_manager import ChessState, ChessPiece, PieceType, PieceColor


class PositionEvaluator:
    """
    Evaluates chess positions to determine relative strength.
    
    This class handles the evaluation of chess positions using various
    heuristics like piece values, mobility, piece-square tables, etc.
    """
    
    def __init__(self):
        """Initialize the position evaluator with evaluation parameters."""
        # Basic piece values (in centipawns)
        self.piece_values = {
            PieceType.PAWN: 100,
            PieceType.KNIGHT: 320,
            PieceType.BISHOP: 330,
            PieceType.ROOK: 500,
            PieceType.QUEEN: 900,
            PieceType.KING: 20000  # High value to prioritize king safety
        }
        
        # Piece-square tables for positional evaluation
        # These tables reflect the ideal squares for each piece type
        self.piece_square_tables = self._init_piece_square_tables()
        
        # Phase weights for transitioning between opening, middlegame and endgame
        self.phase_weights = {
            'opening': 1.0,
            'middlegame': 0.0,
            'endgame': 0.0
        }
    
    def _init_piece_square_tables(self) -> Dict[PieceType, List[List[int]]]:
        """
        Initialize piece-square tables for all piece types.
        
        Returns:
            Dictionary mapping piece types to their piece-square tables
        """
        # For each piece type, provide an 8x8 table of position values
        # Higher values indicate better squares for that piece
        
        # Pawns prefer to advance and control the center
        pawn_table = [
            [  0,   0,   0,   0,   0,   0,   0,   0],
            [ 50,  50,  50,  50,  50,  50,  50,  50],
            [ 10,  10,  20,  30,  30,  20,  10,  10],
            [  5,   5,  10,  25,  25,  10,   5,   5],
            [  0,   0,   0,  20,  20,   0,   0,   0],
            [  5,  -5, -10,   0,   0, -10,  -5,   5],
            [  5,  10,  10, -20, -20,  10,  10,   5],
            [  0,   0,   0,   0,   0,   0,   0,   0]
        ]
        
        # Knights prefer central positions with good outposts
        knight_table = [
            [-50, -40, -30, -30, -30, -30, -40, -50],
            [-40, -20,   0,   0,   0,   0, -20, -40],
            [-30,   0,  10,  15,  15,  10,   0, -30],
            [-30,   5,  15,  20,  20,  15,   5, -30],
            [-30,   0,  15,  20,  20,  15,   0, -30],
            [-30,   5,  10,  15,  15,  10,   5, -30],
            [-40, -20,   0,   5,   5,   0, -20, -40],
            [-50, -40, -30, -30, -30, -30, -40, -50]
        ]
        
        # Bishops prefer diagonal control and open positions
        bishop_table = [
            [-20, -10, -10, -10, -10, -10, -10, -20],
            [-10,   0,   0,   0,   0,   0,   0, -10],
            [-10,   0,  10,  10,  10,  10,   0, -10],
            [-10,   5,   5,  10,  10,   5,   5, -10],
            [-10,   0,   5,  10,  10,   5,   0, -10],
            [-10,   5,   5,   5,   5,   5,   5, -10],
            [-10,   0,   0,   0,   0,   0,   0, -10],
            [-20, -10, -10, -10, -10, -10, -10, -20]
        ]
        
        # Rooks prefer open files and 7th/8th ranks
        rook_table = [
            [  0,   0,   0,   0,   0,   0,   0,   0],
            [  5,  10,  10,  10,  10,  10,  10,   5],
            [ -5,   0,   0,   0,   0,   0,   0,  -5],
            [ -5,   0,   0,   0,   0,   0,   0,  -5],
            [ -5,   0,   0,   0,   0,   0,   0,  -5],
            [ -5,   0,   0,   0,   0,   0,   0,  -5],
            [ -5,   0,   0,   0,   0,   0,   0,  -5],
            [  0,   0,   0,   5,   5,   0,   0,   0]
        ]
        
        # Queens combine mobility of rooks and bishops
        queen_table = [
            [-20, -10, -10,  -5,  -5, -10, -10, -20],
            [-10,   0,   0,   0,   0,   0,   0, -10],
            [-10,   0,   5,   5,   5,   5,   0, -10],
            [ -5,   0,   5,   5,   5,   5,   0,  -5],
            [  0,   0,   5,   5,   5,   5,   0,  -5],
            [-10,   5,   5,   5,   5,   5,   0, -10],
            [-10,   0,   5,   0,   0,   0,   0, -10],
            [-20, -10, -10,  -5,  -5, -10, -10, -20]
        ]
        
        # King prefers safety in the opening/middlegame
        king_table_opening = [
            [-30, -40, -40, -50, -50, -40, -40, -30],
            [-30, -40, -40, -50, -50, -40, -40, -30],
            [-30, -40, -40, -50, -50, -40, -40, -30],
            [-30, -40, -40, -50, -50, -40, -40, -30],
            [-20, -30, -30, -40, -40, -30, -30, -20],
            [-10, -20, -20, -20, -20, -20, -20, -10],
            [ 20,  20,   0,   0,   0,   0,  20,  20],
            [ 20,  30,  10,   0,   0,  10,  30,  20]
        ]
        
        # King becomes more active in the endgame
        king_table_endgame = [
            [-50, -40, -30, -20, -20, -30, -40, -50],
            [-30, -20, -10,   0,   0, -10, -20, -30],
            [-30, -10,  20,  30,  30,  20, -10, -30],
            [-30, -10,  30,  40,  40,  30, -10, -30],
            [-30, -10,  30,  40,  40,  30, -10, -30],
            [-30, -10,  20,  30,  30,  20, -10, -30],
            [-30, -30,   0,   0,   0,   0, -30, -30],
            [-50, -30, -30, -30, -30, -30, -30, -50]
        ]
        
        return {
            PieceType.PAWN: pawn_table,
            PieceType.KNIGHT: knight_table,
            PieceType.BISHOP: bishop_table,
            PieceType.ROOK: rook_table,
            PieceType.QUEEN: queen_table,
            PieceType.KING: king_table_opening,  # Use opening table by default
        }
        
    def get_game_phase(self, state: ChessState) -> Dict[str, float]:
        """
        Determine the current phase of the game.
        
        Args:
            state: Current chess game state
            
        Returns:
            Dictionary with weights for each game phase (opening, middlegame, endgame)
        """
        # Count material to determine game phase
        total_material = 0
        for piece in state.board.values():
            if piece.piece_type != PieceType.KING:  # Exclude kings
                total_material += self.piece_values[piece.piece_type]
        
        # Full material (excluding kings) would be:
        # 8 pawns + 2 knights + 2 bishops + 2 rooks + 1 queen per side
        # = 8*100 + 2*320 + 2*330 + 2*500 + 1*900 = 3900 per side = 7800 total
        
        # Phase thresholds (these can be adjusted)
        opening_threshold = 7000    # >90% material remains
        middlegame_threshold = 4000  # ~50% material remains
        endgame_threshold = 1500     # <20% material remains
        
        if total_material > opening_threshold:
            return {'opening': 1.0, 'middlegame': 0.0, 'endgame': 0.0}
        elif total_material > middlegame_threshold:
            # Linear transition from opening to middlegame
            opening_weight = (total_material - middlegame_threshold) / (opening_threshold - middlegame_threshold)
            middlegame_weight = 1.0 - opening_weight
            return {'opening': opening_weight, 'middlegame': middlegame_weight, 'endgame': 0.0}
        elif total_material > endgame_threshold:
            # Linear transition from middlegame to endgame
            middlegame_weight = (total_material - endgame_threshold) / (middlegame_threshold - endgame_threshold)
            endgame_weight = 1.0 - middlegame_weight
            return {'opening': 0.0, 'middlegame': middlegame_weight, 'endgame': endgame_weight}
        else:
            return {'opening': 0.0, 'middlegame': 0.0, 'endgame': 1.0}
    
    def evaluate_material(self, state: ChessState) -> int:
        """
        Evaluate material balance of the position.
        
        Args:
            state: Current chess game state
            
        Returns:
            Material score (positive favors white, negative favors black)
        """
        score = 0
        for piece in state.board.values():
            value = self.piece_values[piece.piece_type]
            if piece.color == PieceColor.WHITE:
                score += value
            else:
                score -= value
        
        return score
    
    def evaluate_piece_position(self, state: ChessState) -> int:
        """
        Evaluate piece positions using piece-square tables.
        
        Args:
            state: Current chess game state
            
        Returns:
            Position score (positive favors white, negative favors black)
        """
        score = 0
        
        # Get current game phase
        phase = self.get_game_phase(state)
        
        # Create a blended king table based on game phase
        king_table_opening = self.piece_square_tables[PieceType.KING]
        king_table_endgame = [
            [-50, -40, -30, -20, -20, -30, -40, -50],
            [-30, -20, -10,   0,   0, -10, -20, -30],
            [-30, -10,  20,  30,  30,  20, -10, -30],
            [-30, -10,  30,  40,  40,  30, -10, -30],
            [-30, -10,  30,  40,  40,  30, -10, -30],
            [-30, -10,  20,  30,  30,  20, -10, -30],
            [-30, -30,   0,   0,   0,   0, -30, -30],
            [-50, -30, -30, -30, -30, -30, -30, -50]
        ]
        
        # Evaluate each piece's position
        for (x, y), piece in state.board.items():
            if piece.piece_type == PieceType.KING:
                # Blend king tables based on game phase
                table_value = (
                    king_table_opening[y][x] * (phase['opening'] + phase['middlegame']) +
                    king_table_endgame[y][x] * phase['endgame']
                )
            else:
                table_value = self.piece_square_tables[piece.piece_type][y][x]
            
            # White pieces use the tables as-is
            if piece.color == PieceColor.WHITE:
                score += table_value
            # Black pieces use the tables flipped vertically
            else:
                flipped_y = 7 - y
                score -= self.piece_square_tables[piece.piece_type][flipped_y][x]
        
        return score
    
    def evaluate_mobility(self, state: ChessState, mobility_factor: float = 0.1) -> int:
        """
        Evaluate piece mobility (number of legal moves).
        
        Args:
            state: Current chess game state
            mobility_factor: Weight for mobility score
            
        Returns:
            Mobility score (positive favors white, negative favors black)
        """
        # This is a simplified version - a real implementation would count
        # the number of legal moves for each side
        
        # For now, return 0 as a placeholder
        return 0
    
    def evaluate_king_safety(self, state: ChessState) -> int:
        """
        Evaluate king safety based on pawn shield, piece proximity, etc.
        
        Args:
            state: Current chess game state
            
        Returns:
            King safety score (positive favors white, negative favors black)
        """
        # This is a simplified version - a real implementation would evaluate:
        # - Pawn shield in front of the king
        # - Castled position
        # - Open files near the king
        # - Enemy piece attacks near the king
        return 0
    
    def evaluate(self, state: ChessState) -> int:
        """
        Evaluate the overall position.
        
        Args:
            state: Current chess game state
            
        Returns:
            Position score (positive favors white, negative favors black)
        """
        # Get phase weights to determine how to weigh different factors
        phase = self.get_game_phase(state)
        
        # Material evaluation (most important component)
        material_score = self.evaluate_material(state)
        
        # Piece position evaluation
        position_score = self.evaluate_piece_position(state)
        
        # Mobility evaluation (more important in middlegame/endgame)
        mobility_score = self.evaluate_mobility(state)
        mobility_weight = 0.1 * phase['middlegame'] + 0.2 * phase['endgame']
        
        # King safety (more important in opening/middlegame)
        king_safety_score = self.evaluate_king_safety(state)
        king_safety_weight = 0.3 * phase['opening'] + 0.2 * phase['middlegame']
        
        # Combine all factors into final score
        final_score = (
            material_score +
            position_score +
            mobility_score * mobility_weight +
            king_safety_score * king_safety_weight
        )
        
        return final_score

