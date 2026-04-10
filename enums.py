"""Enumerations for the Tower Defense game.

Defines all enum types used across the game: tower types, enemy types,
game states, and soldier states.
"""

from enum import Enum, auto


class TowerType(Enum):
    """Types of towers the player can build."""
    ARCHER = auto()
    MAGE = auto()
    ARTILLERY = auto()
    BARRACKS = auto()


class EnemyType(Enum):
    """Types of enemies that spawn in waves."""
    GRUNT = auto()
    RUNNER = auto()
    ARMORED = auto()
    BOSS = auto()


class GameState(Enum):
    """Possible states of the game."""
    MENU = auto()
    PLAYING = auto()
    PAUSED = auto()
    GAME_OVER = auto()


class SoldierState(Enum):
    """State machine states for barracks soldiers."""
    IDLE = auto()
    MOVING = auto()
    FIGHTING = auto()
    DYING = auto()
