"""
Chess AI module for Eve AI Vtuber.

This module provides chess game functionality and AI capabilities for Eve,
allowing her to play chess against users on various platforms.
"""

__version__ = '0.1.0'

from .state_manager import ChessState, ChessPiece, PieceType, PieceColor
from .move_generator import MoveGenerator
from .evaluation import PositionEvaluator
from .ai_engine import ChessAI
from .game_controller import ChessGameController

__all__ = [
    'ChessState',
    'ChessPiece',
    'PieceType',
    'PieceColor',
    'MoveGenerator',
    'PositionEvaluator',
    'ChessAI',
    'ChessGameController',
]

