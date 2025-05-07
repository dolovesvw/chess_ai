"""
Chess AI engine module.

This module implements a chess AI using minimax with alpha-beta pruning
for move selection and evaluation.
"""

import time
import random
from typing import List, Tuple, Optional, Dict, Any

from .state_manager import ChessState, PieceType, PieceColor
from .move_generator import MoveGenerator
from .evaluation import PositionEvaluator


class ChessAI:
    """
    Chess AI engine that selects moves using minimax with alpha-beta pruning.
    
    This class implements the core AI decision-making for chess, using position
    evaluation and search algorithms to find strong moves.
    """
    
    def __init__(self, difficulty: int = 3):
        """
        Initialize the chess AI with the specified difficulty.
        
        Args:
            difficulty: Difficulty level (1-5), affects search depth and evaluation
        """
        self.move_generator = MoveGenerator()
        self.evaluator = PositionEvaluator()
        self.max_depth = self._get_depth_for_difficulty(difficulty)
        self.difficulty = difficulty
        self.time_limit = 5.0  # Default time limit in seconds
        self.nodes_searched = 0
        self.transposition_table: Dict[str, Dict[str, Any]] = {}  # Position cache
        
    def _get_depth_for_difficulty(self, difficulty: int) -> int:
        """
        Convert difficulty level to search depth.
        
        Args:
            difficulty: Difficulty level (1-5)
            
        Returns:
            Maximum search depth for the given difficulty
        """
        # Map difficulty levels to search depths
        difficulty_depth_map = {
            1: 2,  # Beginner: 2-ply search
            2: 3,  # Easy: 3-ply search
            3: 4,  # Medium: 4-ply search
            4: 5,  # Hard: 5-ply search
            5: 6   # Expert: 6-ply search
        }
        
        return difficulty_depth_map.get(difficulty, 4)  # Default to medium
    
    def set_difficulty(self, difficulty: int) -> None:
        """
        Set the AI difficulty level.
        
        Args:
            difficulty: Difficulty level (1-5)
        """
        self.difficulty = difficulty
        self.max_depth = self._get_depth_for_difficulty(difficulty)
    
    def set_time_limit(self, seconds: float) -> None:
        """
        Set the time limit for move calculation.
        
        Args:
            seconds: Time limit in seconds
        """
        self.time_limit = seconds
    
    def get_best_move(self, state: ChessState) -> Optional[Tuple[Tuple[int, int], Tuple[int, int]]]:
        """
        Find the best move for the current player.
        
        Args:
            state: Current chess state
            
        Returns:
            Best move as ((from_x, from_y), (to_x, to_y)) tuple, or None if no legal moves
        """
        # Reset search statistics
        self.nodes_searched = 0
        start_time = time.time()
        
        # Get all legal moves
        legal_moves = self.move_generator.generate_moves(state)
        
        if not legal_moves:
            return None
        
        # If only one legal move, return it immediately
        if len(legal_moves) == 1:
            return legal_moves[0]
        
        # For very low difficulty, just return a random move
        if self.difficulty == 1 and random.random() < 0.3:
            return random.choice(legal_moves)
        
        # Use iterative deepening to better manage time
        best_move = None
        best_value = float('-inf') if state.active_color == PieceColor.WHITE else float('inf')
        
        # Start with depth 1 and increase up to max_depth
        for current_depth in range(1, self.max_depth + 1):
            # Order moves using move ordering from previous iteration
            ordered_moves = self._order_moves(legal_moves, state)
            
            alpha = float('-inf')
            beta = float('inf')
            
            # White is maximizing player, black is minimizing
            if state.active_color == PieceColor.WHITE:
                best_value = float('-inf')
                for move in ordered_moves:
                    # Make a copy of the state to avoid modifying the original
                    new_state = self._make_move_copy(state, move)
                    
                    value = self._alpha_beta(new_state, current_depth - 1, alpha, beta, False)
                    
                    if value > best_value:
                        best_value = value
                        best_move = move
                    
                    alpha = max(alpha, best_value)
            else:
                best_value = float('inf')
                for move in ordered_moves:
                    new_state = self._make_move_copy(state, move)
                    
                    value = self._alpha_beta(new_state, current_depth - 1, alpha, beta, True)
                    
                    if value < best_value:
                        best_value = value
                        best_move = move
                    
                    beta = min(beta, best_value)
            
            # Check if time limit is approaching
            elapsed_time = time.time() - start_time
            if elapsed_time > self.time_limit * 0.8:  # Use 80% of time limit as cutoff
                break
        
        # Add some randomness to weaker difficulty levels to make the AI less predictable
        if self.difficulty <= 2 and random.random() < 0.2:
            alternative_moves = [move for move in legal_moves if move != best_move]
            if alternative_moves:
                best_move = random.choice(alternative_moves)
        
        return best_move
    
    def _alpha_beta(self, state: ChessState, depth: int, alpha: float, beta: float, 
                   maximizing_player: bool) -> float:
        """
        Perform alpha-beta pruning search to evaluate positions.
        
        Args:
            state: Current chess state
            depth: Remaining search depth
            alpha: Alpha value for pruning
            beta: Beta value for pruning
            maximizing_player: True if current player is maximizing (white)
            
        Returns:
            Position score
        """
        # Increment node counter
        self.nodes_searched += 1
        
        # Check for terminal conditions
        if depth == 0 or state.is_checkmate() or state.is_stalemate():
            return self._evaluate_position(state)
        
        legal_moves = self.move_generator.generate_moves(state)
        
        # No legal moves - checkmate or stalemate
        if not legal_moves:
            if state.is_check():  # Checkmate
                return float('-inf') if maximizing_player else float('inf')
            else:  # Stalemate
                return 0
        
        # Order moves for better pruning
        ordered_moves = self._order_moves(legal_moves, state)
        
        if maximizing_player:
            value = float('-inf')
            for move in ordered_moves:
                new_state = self._make_move_copy(state, move)
                value = max(value, self._alpha_beta(new_state, depth - 1, alpha, beta, False))
                alpha = max(alpha, value)
                if alpha >= beta:
                    break  # Beta cutoff
            return value
        else:
            value = float('inf')
            for move in ordered_moves:
                new_state = self._make_move_copy(state, move)
                value = min(value, self._alpha_beta(new_state, depth - 1, alpha, beta, True))
                beta = min(beta, value)
                if beta <= alpha:
                    break  # Alpha cutoff
            return value
    
    def _make_move_copy(self, state: ChessState, move: Tuple[Tuple[int, int], Tuple[int, int]]) -> ChessState:
        """
        Create a new state with the move applied.
        
        Args:
            state: Original chess state
            move: Move to apply as ((from_x, from_y), (to_x, to_y))
            
        Returns:
            New chess state with the move applied
        """
        # This is a simplified implementation
        # A more complete version would handle special moves properly
        from_pos, to_pos = move
        from_x, from_y = from_pos
        to_x, to_y = to_pos
        
        # Create a deep copy of the state
        new_state = ChessState()
        new_state.board = state.board.copy()
        new_state.active_color = state.active_color
        new_state.castling_rights = {
            color: rights[:] for color, rights in state.castling_rights.items()
        }
        new_state.en_passant_target = state.en_passant_target
        new_state.halfmove_clock = state.halfmove_clock
        new_state.fullmove_number = state.fullmove_number
        new_state.move_history = state.move_history.copy()
        
        # Apply the move
        new_state.make_move(from_x, from_y, to_x, to_y)
        
        return new_state
    
    def _order_moves(self, moves: List[Tuple[Tuple[int, int], Tuple[int, int]]], 
                    state: ChessState) -> List[Tuple[Tuple[int, int], Tuple[int, int]]]:
        """
        Order moves to optimize alpha-beta pruning.
        
        Args:
            moves: List of legal moves
            state: Current chess state
            
        Returns:
            Ordered list of moves (best moves first)
        """
        # This is a simple move ordering:
        # 1. Captures - sorted by value of captured piece - value of capturing piece
        # 2. Checks
        # 3. Other moves
        
        # For simplicity, we'll just prioritize captures for now
        move_scores = []
        
        for move in moves:
            from_pos, to_pos = move
            from_x, from_y = from_pos
            to_x, to_y = to_pos
            
            score = 0
            
            # Get moving piece
            moving_piece = state.get_piece_at(from_x, from_y)
            if moving_piece is None:
                continue
                
            # Check if capture (piece at target square)
            target_piece = state.get_piece_at(to_x, to_y)
            if target_piece is not None:
                # MVV-LVA (Most Valuable Victim - Least Valuable Aggressor)
                # Score captures higher based on value of captured piece minus value of capturing piece
                moving_value = self.evaluator.piece_values[moving_piece.piece_type]
                target_value = self.evaluator.piece_values[target_piece.piece_type]
                score = target_value - (moving_value // 10)
            
            # Add positional improvement score
            # Higher scores for moves to better squares according to piece-square tables
            current_sq_value = self.evaluator.piece_square_tables[moving_piece.piece_type][from_y][from_x]
            new_sq_value = self.evaluator.piece_square_tables[moving_piece.piece_type][to_y][to_x]
            positional_improvement = new_sq_value - current_sq_value
            
            score += positional_improvement // 10
            
            move_scores.append((move, score))
        
        # Sort by score, highest first
        move_scores.sort(key=lambda x: x[1], reverse=True)
        
        # Extract just the moves from the sorted list
        return [move for move, _ in move_scores]
    
    def _evaluate_position(self, state: ChessState) -> float:
        """
        Evaluate the current chess position.
        
        Args:
            state: The chess state to evaluate
            
        Returns:
            Position score (positive favors white, negative favors black)
        """
        # Use the PositionEvaluator to get a score
        score = self.evaluator.evaluate(state)
        
        # Add a small random factor to prevent repetition and add variety
        noise = random.uniform(-5, 5)
        score += noise
        
        return score
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about the last search.
        
        Returns:
            Dictionary with search statistics
        """
        return {
            "nodes_searched": self.nodes_searched,
            "max_depth": self.max_depth,
            "difficulty": self.difficulty,
            "time_limit": self.time_limit
        }

"""
Chess AI engine module.

This module implements a chess AI using minimax with alpha-beta pruning
for move selection and evaluation.
"""

import time
import random
from typing import List, Tuple, Optional, Dict, Any

from .state_manager import ChessState, PieceType, PieceColor
from .move_generator import MoveGenerator
from .evaluation import PositionEvaluator


class ChessAI:
    """
    Chess AI engine that selects moves using minimax with alpha-beta pruning.
    
    This class implements the core AI decision-making for chess, using position
    evaluation and search algorithms to find strong moves.
    """
    
    def __init__(self, difficulty: int = 3):
        """
        Initialize the chess AI with the specified difficulty.
        
        Args:
            difficulty: Difficulty level (1-5), affects search depth and evaluation
        """
        self.move_generator = MoveGenerator()
        self.evaluator = PositionEvaluator()
        self.max_depth = self._get_depth_for_difficulty(difficulty)
        self.difficulty = difficulty
        self.time_limit = 5.0  # Default time limit in seconds
        self.nodes_searched = 0
        self.transposition_table: Dict[str, Dict[str, Any]] = {}  # Position cache
        
    def _get_depth_for_difficulty(self, difficulty: int) -> int:
        """
        Convert difficulty level to search depth.
        
        Args:
            difficulty: Difficulty level (1-5)
            
        Returns:
            Maximum search depth for the given difficulty
        """
        # Map difficulty levels to search depths
        difficulty_depth_map = {
            1: 2,  # Beginner: 2-ply search
            2: 3,  # Easy: 3-ply search
            3: 4,  # Medium: 4-ply search
            4: 5,  # Hard: 5-ply search
            5: 6   # Expert: 6-ply search
        }
        
        return difficulty_depth_map.get(difficulty, 4)  # Default to medium
    
    def set_difficulty(self, difficulty: int) -> None:
        """
        Set the AI difficulty level.
        
        Args:
            difficulty: Difficulty level (1-5)
        """
        self.difficulty = difficulty
        self.max_depth = self._get_depth_for_difficulty(difficulty)
    
    def set_time_limit(self, seconds: float) -> None:
        """
        Set the time limit for move calculation.
        
        Args:
            seconds: Time limit in seconds
        """
        self.time_limit = seconds
    
    def get_best_move(self, state: ChessState) -> Optional[Tuple[Tuple[int, int], Tuple[int, int]]]:
        """
        Find the best move for the current player.
        
        Args:
            state: Current chess state
            
        Returns:
            Best move as ((from_x, from_y), (to_x, to_y)) tuple, or None if no legal moves
        """
        # Reset search statistics
        self.nodes_searched = 0
        start_time = time.time()
        
        # Get all legal moves
        legal_moves = self.move_generator.generate_moves(state)
        
        if not legal_moves:
            return None
        
        # If only one legal move, return it immediately
        if len(legal_moves) == 1:
            return legal_moves[0]
        
        # For very low difficulty, just return a random move
        if self.difficulty == 1 and random.random() < 0.3:
            return random.choice(legal_moves)
        
        # Use iterative deepening to better manage time
        best_move = None
        best_value = float('-inf') if state.active_color == PieceColor.WHITE else float('inf')
        
        # Start with depth 1 and increase up to max_depth
        for current_depth in range(1, self.max_depth + 1):
            # Order moves using move ordering from previous iteration
            ordered_moves = self._order_moves(legal_moves, state)
            
            alpha = float('-inf')
            beta = float('inf')
            
            # White is maximizing player, black is minimizing
            if state.active_color == PieceColor.WHITE:
                best_value = float('-inf')
                for move in ordered_moves:
                    # Make a copy of the state to avoid modifying the original
                    new_state = self._make_move_copy(state, move)
                    
                    value = self._alpha_beta(new_state, current_depth - 1, alpha, beta, False)
                    
                    if value > best_value:
                        best_value = value
                        best_move = move
                    
                    alpha = max(alpha, best_value)
            else:
                best_value = float('inf')
                for move in ordered_moves:
                    new_state = self._make_move_copy(state, move)
                    
                    value = self._alpha_beta(new_state, current_depth - 1, alpha, beta, True)
                    
                    if value < best_value:
                        best_value = value
                        best_move = move
                    
                    beta = min(beta, best_value)
            
            # Check if time limit is approaching
            elapsed_time = time.time() - start_time
            if elapsed_time > self.time_limit * 0.8:  # Use 80% of time limit as cutoff
                break
        
        # Add some randomness to weaker difficulty levels to make the AI less predictable
        if self.difficulty <= 2 and random.random() < 0.2:
            alternative_moves = [move for move in legal_moves if move != best_move]
            if alternative_moves:
                best_move = random.choice(alternative_moves)
        
        return best_move
    
    def _alpha_beta(self, state: ChessState, depth: int, alpha: float, beta: float, 
                   maximizing_player: bool) -> float:
        """
        Perform alpha-beta pruning search to evaluate positions.
        
        Args:
            state: Current chess state
            depth: Remaining search depth
            alpha: Alpha value for pruning
            beta: Beta value for pruning
            maximizing_player: True if current player is maximizing (white)
            
        Returns:
            Position score
        """
        # Increment node counter
        self.nodes_searched += 1
        
        # Check for terminal conditions
        if depth == 0 or state.is_checkmate() or state.is_stalemate():
            return self._evaluate_position(state)
        
        legal_moves = self.move_generator.generate_moves(state)
        
        # No legal moves - checkmate or stalemate
        if not legal_moves:
            if state.is_check():  # Checkmate
                return float('-inf') if maximizing_player else float('inf')
            else:  # Stalemate
                return 0
        
        # Order moves for better pruning
        ordered_moves = self._order_moves(legal_moves, state)
        
        if maximizing_player:
            value = float('-inf')
            for move in ordered_moves:
                new_state = self._make_move_copy(state, move)
                value = max(value, self._alpha_beta(new_state, depth - 1, alpha, beta, False))
                alpha = max(alpha, value)
                if alpha >= beta:
                    break  # Beta cutoff
            return value
        else:
            value = float('inf')
            for move in ordered_moves:
                new_state = self._make_move_copy(state, move)
                value = min(value, self._alpha_beta(new_state, depth - 1, alpha, beta, True))
                beta = min(beta, value)
                if beta <= alpha:
                    break  # Alpha cutoff
            return value
    
    def _make_move_copy(self, state: ChessState, move: Tuple[Tuple[int, int], Tuple[int, int]]) -> ChessState:
        """
        Create a new state with the move applied.
        
        Args:
            state: Original chess state
            move: Move to apply as ((from_x, from_y), (to_x, to_y))
            
        Returns:
            New chess state with the move applied
        """
        # This is a simplified implementation
        # A more complete version would handle special moves properly
        from_pos, to_pos = move
        from_x, from_y = from_pos
        to_x, to_y = to_pos
        
        # Create a deep copy of the state
        new_state = ChessState()
        new_state.board = state.board.copy()
        new_state.active_color = state.active_color
        new_state.castling_rights = {
            color: rights[:] for color, rights in state.castling_rights.items()
        }
        new_state.en_passant_target = state.en_passant_target
        new_state.halfmove_clock = state.halfmove_clock
        new_state.fullmove_number = state.fullmove_number
        new_state.move_history = state.move_history.copy()
        
        # Apply the move
        new_state.make_move(from_x, from_y, to_x, to_y)
        
        return new_state
    
    def _order_moves(self, moves: List[Tuple[Tuple[int, int], Tuple[int, int]]], 
                    state: ChessState) -> List[Tuple[Tuple[int, int], Tuple[int, int]]]:
        """
        Order moves to optimize alpha-beta pruning.
        
        Args:
            moves: List of legal moves
            state: Current chess state
            
        Returns:
            Ordered list of moves (best moves first)
        """
        # This is a simple move ordering:
        # 1. Captures - sorted by value of captured piece - value of capturing piece
        # 2. Checks
        # 3. Other moves
        
        # For simplicity, we'll just prioritize captures for now
        move_scores = []
        
        for move in moves:
            from_pos, to_pos = move
            from_x, from_y = from_pos
            to_x, to_y = to_pos
            
            score = 0
            
            # Get moving piece
            moving_piece = state.get_piece_at(from_x, from_y)
            if moving_piece is None:
                continue
                
            # Check if capture (piece at target square)
            target_piece = state.get_piece_at(to_x, to_y)
            if target_piece is not None:
                # MVV-LVA (Most Valuable Victim - Least Valuable Aggressor)
                # Score captures higher based on value of captured piece minus value of capturing piece
                moving_value = self.evaluator.piece_values[moving_piece.piece_type]
                target_value = self.evaluator.piece_values[target_piece.piece_type]
                score = target_value - (moving_value // 10)
            
            # Add positional improvement score
            # Higher scores for moves to better squares according to piece-square tables
            current_sq_value = self.evaluator.piece_square_tables[moving_piece.piece_type][from_y][from_x]
            new_sq_value = self.evaluator.piece_square_tables[moving_piece.piece_type][to_y][to_x]
            positional_improvement = new_sq_value - current_sq_value
            
            score += positional_improvement // 10
            
            move_scores.append((move, score))
        
        # Sort by score, highest first
        move_scores.sort(key=lambda x: x[1], reverse=True)
        
        # Extract just the moves from the sorted list
        return [move for move, _ in move_scores]
    
    def _evaluate_position(self, state: ChessState) -> float:
        """
        Evaluate the current chess position.
        
        Args:
            state: The chess state to evaluate
            
        Returns:
            Position score (positive favors white, negative favors black)
        """
        # Use the PositionEvaluator to get a score
        score = self.evaluator.evaluate(state)
        
        # Add a small random factor to prevent repetition and add variety
        noise = random.uniform(-5, 5)
        score += noise
        
        return score
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about the last search.
        
        Returns:
            Dictionary with search statistics
        """
        return {
            "nodes_searched": self.nodes_searched,
            "max_depth": self.max_depth,
            "difficulty": self.difficulty,
            "time_limit": self.time_limit
        }

