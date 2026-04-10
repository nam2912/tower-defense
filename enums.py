"""Enumerations for the Tower Defense game.

Defines all enum types used across the game: tower types, enemy types,
game states, and soldier states.
"""

from enum import Enum, auto


class TowerType(Enum):
    """Types of towers the player can build."""
    FORTRESS = auto()
    ARCHER = auto()
    BARRACKS = auto()
    MAGE = auto()
    ARTILLERY = auto()
    FREEZE = auto()
    POISON = auto()
    BALLISTA = auto()
    TESLA = auto()
    NECROMANCER = auto()
    LASER = auto()


class EnemyType(Enum):
    """Types of enemies that spawn in waves."""
    GRUNT = auto()
    RUNNER = auto()
    ARMORED = auto()
    BOMBER = auto()
    BOSS = auto()


class GameState(Enum):
    """Possible states of the game."""
    MENU = auto()
    PLAYING = auto()
    PAUSED = auto()
    ROUND_COMPLETE = auto()
    ROUND_FAILED = auto()
    GAME_OVER = auto()


class SoldierState(Enum):
    """State machine states for barracks soldiers."""
    IDLE = auto()
    MOVING = auto()
    FIGHTING = auto()
    DYING = auto()
