"""
Chess state management module.

This module handles the representation and manipulation of chess game states,
including the board, pieces, and game rules.
"""

import enum
from typing import Dict, List, Optional, Tuple, Set


class PieceType(enum.Enum):
    """Chess piece types."""
    PAWN = 'p'
    KNIGHT = 'n'
    BISHOP = 'b'
    ROOK = 'r'
    QUEEN = 'q'
    KING = 'k'


class PieceColor(enum.Enum):
    """Chess piece colors."""
    WHITE = 'w'
    BLACK = 'b'


class ChessPiece:
    """Represents a chess piece."""
    
    def __init__(self, piece_type: PieceType, color: PieceColor):
        """
        Initialize a chess piece.
        
        Args:
            piece_type: The type of the piece (pawn, knight, etc.)
            color: The color of the piece (white or black)
        """
        self.piece_type = piece_type
        self.color = color
        
    def __str__(self) -> str:
        """Return string representation of the piece."""
        char = self.piece_type.value
        return char.upper() if self.color == PieceColor.WHITE else char.lower()
    
    def __repr__(self) -> str:
        """Return detailed string representation of the piece."""
        return f"ChessPiece({self.piece_type}, {self.color})"


class ChessState:
    """
    Represents the state of a chess game.
    
    This class handles the board representation, move validation,
    and game state tracking (check, checkmate, stalemate, etc.)
    """
    
    def __init__(self):
        """Initialize a new chess game with the starting position."""
        # Board representation: dictionary mapping coordinates (x, y) to pieces
        # (0, 0) is bottom-left (a1), (7, 7) is top-right (h8)
        self.board: Dict[Tuple[int, int], ChessPiece] = {}
        
        # Game state variables
        self.active_color: PieceColor = PieceColor.WHITE
        self.castling_rights: Dict[PieceColor, Tuple[bool, bool]] = {
            PieceColor.WHITE: (True, True),  # (queenside, kingside)
            PieceColor.BLACK: (True, True),
        }
        self.en_passant_target: Optional[Tuple[int, int]] = None
        self.halfmove_clock: int = 0  # Moves since last capture or pawn advance
        self.fullmove_number: int = 1  # Incremented after Black's move
        
        # Move history
        self.move_history: List[str] = []
        
        # Setup the initial board position
        self._setup_initial_position()
    
    def _setup_initial_position(self) -> None:
        """Set up the initial chess position."""
        # Set up pawns
        for x in range(8):
            self.board[(x, 1)] = ChessPiece(PieceType.PAWN, PieceColor.WHITE)
            self.board[(x, 6)] = ChessPiece(PieceType.PAWN, PieceColor.BLACK)
        
        # Set up other pieces
        back_rank = [
            PieceType.ROOK, PieceType.KNIGHT, PieceType.BISHOP, PieceType.QUEEN,
            PieceType.KING, PieceType.BISHOP, PieceType.KNIGHT, PieceType.ROOK
        ]
        
        for x, piece_type in enumerate(back_rank):
            self.board[(x, 0)] = ChessPiece(piece_type, PieceColor.WHITE)
            self.board[(x, 7)] = ChessPiece(piece_type, PieceColor.BLACK)
    
    def get_piece_at(self, x: int, y: int) -> Optional[ChessPiece]:
        """
        Get the piece at the specified position.
        
        Args:
            x: File (column) coordinate (0-7)
            y: Rank (row) coordinate (0-7)
            
        Returns:
            The piece at the position, or None if empty
        """
        return self.board.get((x, y))
    
    def is_valid_move(self, from_x: int, from_y: int, to_x: int, to_y: int) -> bool:
        """
        Check if a move is valid according to chess rules.
        
        Args:
            from_x: Starting file coordinate
            from_y: Starting rank coordinate
            to_x: Target file coordinate
            to_y: Target rank coordinate
            
        Returns:
            True if the move is valid, False otherwise
        """
        # This is a stub that will need to be implemented with full chess rules
        # In a complete implementation, this would check:
        # - If the piece can move that way
        # - If the move would leave the king in check
        # - Special rules like castling, en passant, etc.
        return True
    
    def make_move(self, from_x: int, from_y: int, to_x: int, to_y: int, promotion: Optional[PieceType] = None) -> bool:
        """
        Make a chess move if it's valid.
        
        Args:
            from_x: Starting file coordinate
            from_y: Starting rank coordinate
            to_x: Target file coordinate
            to_y: Target rank coordinate
            promotion: Piece type to promote to (if move is a pawn promotion)
            
        Returns:
            True if the move was made, False if invalid
        """
        if not self.is_valid_move(from_x, from_y, to_x, to_y):
            return False
        
        # This is a simplified version - a full implementation would:
        # - Update the board state
        # - Handle captures
        # - Update castling rights
        # - Handle special moves (castling, en passant, promotion)
        # - Update game state variables
        # - Check for game end conditions
        
        # Example basic move implementation:
        piece = self.board.pop((from_x, from_y))
        self.board[(to_x, to_y)] = piece
        
        # Switch active color
        self.active_color = (
            PieceColor.BLACK if self.active_color == PieceColor.WHITE else PieceColor.WHITE
        )
        
        # Update move counters
        if self.active_color == PieceColor.WHITE:
            self.fullmove_number += 1
            
        # Update move history (in algebraic notation)
        # This is a simplified placeholder - proper algebraic notation would be implemented
        move_text = f"{chr(97 + from_x)}{from_y + 1}{chr(97 + to_x)}{to_y + 1}"
        self.move_history.append(move_text)
        
        return True
    
    def is_check(self) -> bool:
        """
        Determine if the current player's king is in check.
        
        Returns:
            True if the current player is in check, False otherwise
        """
        # Implementation will check if any opponent piece can capture the king
        return False
    
    def is_checkmate(self) -> bool:
        """
        Determine if the current player is in checkmate.
        
        Returns:
            True if the current player is in checkmate, False otherwise
        """
        # Implementation will check if:
        # 1. The king is in check
        # 2. There are no legal moves that get out of check
        return False
    
    def is_stalemate(self) -> bool:
        """
        Determine if the position is a stalemate.
        
        Returns:
            True if the current player has no legal moves but is not in check
        """
        # Implementation will check if:
        # 1. The king is not in check
        # 2. There are no legal moves
        return False
    
    def get_fen(self) -> str:
        """
        Get the Forsyth-Edwards Notation (FEN) representation of the current position.
        
        Returns:
            FEN string representation of the position
        """
        # This is a placeholder - full FEN implementation would be needed
        return "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
    
    def set_from_fen(self, fen: str) -> None:
        """
        Set the board position from a FEN string.
        
        Args:
            fen: Forsyth-Edwards Notation string
        """
        # This is a placeholder - full FEN parsing would be implemented
        pass

    def get_legal_moves(self) -> List[Tuple[Tuple[int, int], Tuple[int, int]]]:
        """
        Get all legal moves for the current player.
        
        Returns:
            List of legal moves as ((from_x, from_y), (to_x, to_y)) tuples
        """
        # This is a placeholder - a complete implementation would generate
        # all legal moves according to chess rules
        return []
    
    def algebraic_to_coords(self, algebraic: str) -> Tuple[int, int, int, int]:
        """
        Convert algebraic notation (e.g., "e2e4") to board coordinates.
        
        Args:
            algebraic: Move in algebraic notation (e.g., "e2e4")
            
        Returns:
            Tuple of (from_x, from_y, to_x, to_y) coordinates
            
        Raises:
            ValueError: If the algebraic notation is invalid
        """
        if len(algebraic) < 4:
            raise ValueError(f"Invalid algebraic notation: {algebraic}")
        
        from_file = ord(algebraic[0]) - ord('a')
        from_rank = int(algebraic[1]) - 1
        to_file = ord(algebraic[2]) - ord('a')
        to_rank = int(algebraic[3]) - 1
        
        if not (0 <= from_file <= 7 and 0 <= from_rank <= 7 and 
                0 <= to_file <= 7 and 0 <= to_rank <= 7):
            raise ValueError(f"Invalid coordinates in algebraic notation: {algebraic}")
        
        return from_file, from_rank, to_file, to_rank
    
    def coords_to_algebraic(self, from_x: int, from_y: int, to_x: int, to_y: int) -> str:
        """
        Convert board coordinates to algebraic notation.
        
        Args:
            from_x: Starting file coordinate
            from_y: Starting rank coordinate
            to_x: Target file coordinate
            to_y: Target rank coordinate
            
        Returns:
            Move in algebraic notation (e.g., "e2e4")
        """
        return f"{chr(97 + from_x)}{from_y + 1}{chr(97 + to_x)}{to_y + 1}"

