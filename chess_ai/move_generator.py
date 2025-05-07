"""
Chess move generation module.

This module handles the generation of legal chess moves for a given board position.
"""

from typing import Dict, List, Tuple, Set

from .state_manager import ChessState, ChessPiece, PieceType, PieceColor


class MoveGenerator:
    """
    Generates legal chess moves for a given position.
    
    This class handles the complex rules of chess move generation,
    including special moves like castling and en passant.
    """
    
    def __init__(self):
        """Initialize the move generator."""
        # Direction vectors for different piece movements
        # (dx, dy) pairs for each direction
        self.directions = {
            PieceType.PAWN: [],  # Pawns have special movement rules
            PieceType.KNIGHT: [(1, 2), (2, 1), (2, -1), (1, -2), (-1, -2), (-2, -1), (-2, 1), (-1, 2)],
            PieceType.BISHOP: [(1, 1), (1, -1), (-1, -1), (-1, 1)],
            PieceType.ROOK: [(1, 0), (0, 1), (-1, 0), (0, -1)],
            PieceType.QUEEN: [(1, 0), (0, 1), (-1, 0), (0, -1), (1, 1), (1, -1), (-1, -1), (-1, 1)],
            PieceType.KING: [(1, 0), (0, 1), (-1, 0), (0, -1), (1, 1), (1, -1), (-1, -1), (-1, 1)]
        }
        
        # Maximum distance a piece can move in each direction
        self.max_distance = {
            PieceType.PAWN: 1,  # Special handling for initial double move
            PieceType.KNIGHT: 1,
            PieceType.BISHOP: 7,
            PieceType.ROOK: 7,
            PieceType.QUEEN: 7,
            PieceType.KING: 1
        }
    
    def generate_moves(self, state: ChessState) -> List[Tuple[Tuple[int, int], Tuple[int, int]]]:
        """
        Generate all legal moves for the current player.
        
        Args:
            state: Current chess game state
            
        Returns:
            List of legal moves as ((from_x, from_y), (to_x, to_y)) tuples
        """
        legal_moves = []
        active_color = state.active_color
        
        # Find all pieces of the active color
        for (x, y), piece in state.board.items():
            if piece.color != active_color:
                continue
                
            # Generate moves for this piece
            piece_moves = self._generate_piece_moves(state, x, y, piece)
            legal_moves.extend(piece_moves)
        
        return legal_moves
    
    def _generate_piece_moves(self, state: ChessState, x: int, y: int, piece: ChessPiece) -> List[Tuple[Tuple[int, int], Tuple[int, int]]]:
        """
        Generate legal moves for a specific piece.
        
        Args:
            state: Current chess game state
            x: File (column) coordinate of the piece
            y: Rank (row) coordinate of the piece
            piece: The chess piece to generate moves for
            
        Returns:
            List of legal moves for the piece as ((from_x, from_y), (to_x, to_y)) tuples
        """
        moves = []
        from_pos = (x, y)
        
        # Different handling based on piece type
        if piece.piece_type == PieceType.PAWN:
            moves.extend(self._generate_pawn_moves(state, x, y, piece))
        elif piece.piece_type == PieceType.KING:
            moves.extend(self._generate_king_moves(state, x, y, piece))
        else:
            # Handle sliding pieces (knight, bishop, rook, queen)
            directions = self.directions[piece.piece_type]
            max_distance = self.max_distance[piece.piece_type]
            
            for dx, dy in directions:
                for dist in range(1, max_distance + 1):
                    new_x, new_y = x + dx * dist, y + dy * dist
                    
                    # Check if position is on the board
                    if not (0 <= new_x < 8 and 0 <= new_y < 8):
                        break
                        
                    to_pos = (new_x, new_y)
                    target_piece = state.get_piece_at(new_x, new_y)
                    
                    if target_piece is None:
                        # Empty square - valid move
                        moves.append((from_pos, to_pos))
                    elif target_piece.color != piece.color:
                        # Enemy piece - can capture
                        moves.append((from_pos, to_pos))
                        break  # Can't move further in this direction
                    else:
                        # Friendly piece - blocked
                        break
        
        # Filter out moves that would leave the king in check
        legal_moves = []
        for move in moves:
            if not self._would_be_in_check_after_move(state, move):
                legal_moves.append(move)
                
        return legal_moves
    
    def _generate_pawn_moves(self, state: ChessState, x: int, y: int, piece: ChessPiece) -> List[Tuple[Tuple[int, int], Tuple[int, int]]]:
        """Generate legal moves for a pawn."""
        moves = []
        from_pos = (x, y)
        
        # Determine direction based on color
        direction = 1 if piece.color == PieceColor.WHITE else -1
        
        # Forward move
        new_y = y + direction
        if 0 <= new_y < 8 and state.get_piece_at(x, new_y) is None:
            moves.append((from_pos, (x, new_y)))
            
            # Double move from starting position
            if (y == 1 and piece.color == PieceColor.WHITE) or (y == 6 and piece.color == PieceColor.BLACK):
                new_y = y + 2 * direction
                if 0 <= new_y < 8 and state.get_piece_at(x, new_y) is None:
                    moves.append((from_pos, (x, new_y)))
        
        # Captures
        for dx in [-1, 1]:
            new_x, new_y = x + dx, y + direction
            if 0 <= new_x < 8 and 0 <= new_y < 8:
                target_piece = state.get_piece_at(new_x, new_y)
                
                # Regular capture
                if target_piece is not None and target_piece.color != piece.color:
                    moves.append((from_pos, (new_x, new_y)))
                
                # En passant capture
                elif state.en_passant_target == (new_x, new_y):
                    moves.append((from_pos, (new_x, new_y)))
        
        return moves
    
    def _generate_king_moves(self, state: ChessState, x: int, y: int, piece: ChessPiece) -> List[Tuple[Tuple[int, int], Tuple[int, int]]]:
        """Generate legal moves for a king, including castling."""
        moves = []
        from_pos = (x, y)
        
        # Regular king moves
        for dx, dy in self.directions[PieceType.KING]:
            new_x, new_y = x + dx, y + dy
            
            # Check if position is on the board
            if not (0 <= new_x < 8 and 0 <= new_y < 8):
                continue
                
            to_pos = (new_x, new_y)
            target_piece = state.get_piece_at(new_x, new_y)
            
            if target_piece is None or target_piece.color != piece.color:
                # Empty square or enemy piece - valid move
                moves.append((from_pos, to_pos))
        
        # Castling
        if not state.is_check():  # Can't castle out of check
            queenside, kingside = state.castling_rights[piece.color]
            
            # Kingside castling
            if kingside:
                if self._can_castle_kingside(state, x, y, piece.color):
                    moves.append((from_pos, (x + 2, y)))
            
            # Queenside castling
            if queenside:
                if self._can_castle_queenside(state, x, y, piece.color):
                    moves.append((from_pos, (x - 2, y)))
        
        return moves
    
    def _can_castle_kingside(self, state: ChessState, x: int, y: int, color: PieceColor) -> bool:
        """Check if kingside castling is legal."""
        # Check squares between king and rook are empty
        for i in range(1, 3):
            if state.get_piece_at(x + i, y) is not None:
                return False
                
        # Check if squares are under attack
        for i in range(0, 3):
            if self._is_square_attacked(state, x + i, y, color):
                return False
                
        return True
    
    def _can_castle_queenside(self, state: ChessState, x: int, y: int, color: PieceColor) -> bool:
        """Check if queenside castling is legal."""
        # Check squares between king and rook are empty
        for i in range(1, 4):
            if state.get_piece_at(x - i, y) is not None:
                return False
                
        # Check if squares are under attack
        for i in range(0, 3):
            if self._is_square_attacked(state, x - i, y, color):
                return False
                
        return True
    
    def _is_square_attacked(self, state: ChessState, x: int, y: int, color: PieceColor) -> bool:
        """
        Determine if a square is attacked by any piece of the opposite color.
        
        Args:
            state: Current chess state
            x: File (column) coordinate to check
            y: Rank (row) coordinate to check
            color: Color of the piece on the square (to determine attackers)
            
        Returns:
            True if the square is attacked, False otherwise
        """
        opponent_color = PieceColor.BLACK if color == PieceColor.WHITE else PieceColor.WHITE
        
        # Check for pawn attacks
        pawn_direction = -1 if color == PieceColor.WHITE else 1  # Direction pawns attack from
        for dx in [-1, 1]:
            attack_x, attack_y = x + dx, y + pawn_direction
            if 0 <= attack_x < 8 and 0 <= attack_y < 8:
                piece = state.get_piece_at(attack_x, attack_y)
                if (piece is not None and 
                    piece.color == opponent_color and 
                    piece.piece_type == PieceType.PAWN):
                    return True
                    
        # Check for knight attacks
        knight_moves = self.directions[PieceType.KNIGHT]
        for dx, dy in knight_moves:
            attack_x, attack_y = x + dx, y + dy
            if 0 <= attack_x < 8 and 0 <= attack_y < 8:
                piece = state.get_piece_at(attack_x, attack_y)
                if (piece is not None and 
                    piece.color == opponent_color and 
                    piece.piece_type == PieceType.KNIGHT):
                    return True
        
        # Check for king attacks (for adjacent squares)
        king_moves = self.directions[PieceType.KING]
        for dx, dy in king_moves:
            attack_x, attack_y = x + dx, y + dy
            if 0 <= attack_x < 8 and 0 <= attack_y < 8:
                piece = state.get_piece_at(attack_x, attack_y)
                if (piece is not None and 
                    piece.color == opponent_color and 
                    piece.piece_type == PieceType.KING):
                    return True
        
        # Check for sliding piece attacks (bishop, rook, queen)
        # Diagonal directions (bishop, queen)
        diagonal_dirs = self.directions[PieceType.BISHOP]
        for dx, dy in diagonal_dirs:
            for dist in range(1, 8):
                attack_x, attack_y = x + dx * dist, y + dy * dist
                if not (0 <= attack_x < 8 and 0 <= attack_y < 8):
                    break  # Off the board
                    
                piece = state.get_piece_at(attack_x, attack_y)
                if piece is not None:
                    if (piece.color == opponent_color and 
                        (piece.piece_type == PieceType.BISHOP or piece.piece_type == PieceType.QUEEN)):
                        return True
                    break  # Blocked by a piece
        
        # Orthogonal directions (rook, queen)
        orthogonal_dirs = self.directions[PieceType.ROOK]
        for dx, dy in orthogonal_dirs:
            for dist in range(1, 8):
                attack_x, attack_y = x + dx * dist, y + dy * dist
                if not (0 <= attack_x < 8 and 0 <= attack_y < 8):
                    break  # Off the board
                    
                piece = state.get_piece_at(attack_x, attack_y)
                if piece is not None:
                    if (piece.color == opponent_color and 
                        (piece.piece_type == PieceType.ROOK or piece.piece_type == PieceType.QUEEN)):
                        return True
                    break  # Blocked by a piece
        
        return False
    
    def _would_be_in_check_after_move(self, state: ChessState, move: Tuple[Tuple[int, int], Tuple[int, int]]) -> bool:
        """
        Determine if making a move would leave the king in check.
        
        Args:
            state: Current chess state
            move: Move to evaluate as ((from_x, from_y), (to_x, to_y))
            
        Returns:
            True if the move would leave the king in check, False otherwise
        """
        # Create a deep copy of the state
        new_state = self._copy_state(state)
        
        # Apply the move
        from_pos, to_pos = move
        from_x, from_y = from_pos
        to_x, to_y = to_pos
        
        piece = new_state.board.pop((from_x, from_y))
        new_state.board[(to_x, to_y)] = piece
        
        # Find the king's position
        king_pos = None
        for pos, p in new_state.board.items():
            if p.piece_type == PieceType.KING and p.color == state.active_color:
                king_pos = pos
                break
        
        if king_pos is None:
            return False  # No king found (shouldn't happen in a valid chess game)
            
        # Check if the king's position is under attack
        king_x, king_y = king_pos
        return self._is_square_attacked(new_state, king_x, king_y, state.active_color)
    
    def _copy_state(self, state: ChessState) -> ChessState:
        """
        Create a deep copy of a chess state for move validation.
        
        This is a simplified copy that only copies the board and active color,
        which is sufficient for move validation.
        
        Args:
            state: The state to copy
            
        Returns:
            A new ChessState with copied data
        """
        new_state = ChessState()
        
        # Copy board positions (most important for move validation)
        new_state.board = state.board.copy()
        
        # Copy active color
        new_state.active_color = state.active_color
        
        # Copy en passant target
        new_state.en_passant_target = state.en_passant_target
        
        # Copy castling rights
        new_state.castling_rights = {
            color: rights[:] for color, rights in state.castling_rights.items()
        }
        
        return new_state

