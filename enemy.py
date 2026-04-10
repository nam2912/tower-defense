"""Enemy module.

Defines the Enemy class and a factory function to create enemies
by type and wave scaling.

Design patterns: Factory Method.
See REFERENCES.md for full citations.
"""

import math
from enums import EnemyType


class Enemy:
    """Represents an enemy unit moving along the path.

    Attributes:
        enemy_type: The EnemyType enum value.
        x: Current x pixel position.
        y: Current y pixel position.
        hp: Current health points.
        max_hp: Maximum health points.
        speed: Movement speed in pixels per frame.
        armor: Damage reduction value.
        path_index: Index of the next waypoint to move toward.
        is_alive: Whether the enemy is still active.
        gold_reward: Gold earned when this enemy is killed.
    """

    def __init__(self, enemy_type, x, y, hp, speed, armor, gold_reward):
        """Initialize an enemy.

        Args:
            enemy_type: EnemyType enum value.
            x: Starting x pixel position.
            y: Starting y pixel position.
            hp: Health points.
            speed: Movement speed.
            armor: Damage reduction.
            gold_reward: Gold given on kill.
        """
        pass

    def move(self, path_waypoints):
        """Move the enemy toward the next waypoint.

        Args:
            path_waypoints: List of (x, y) pixel waypoints.

        Returns:
            True if the enemy reached the final waypoint (base).
        """
        pass

    def take_damage(self, damage, ignore_armor=False):
        """Apply damage to this enemy, accounting for armor.

        Args:
            damage: Raw damage amount.
            ignore_armor: If True, bypass armor reduction.

        Returns:
            True if the enemy died from this damage.
        """
        pass

    def get_hp_ratio(self):
        """Get the current HP as a ratio of max HP.

        Returns:
            Float between 0.0 and 1.0.
        """
        pass


def create_enemy(enemy_type, start_pos, config, wave_number):
    """Factory function to create an enemy with wave-scaled stats.

    Args:
        enemy_type: EnemyType enum value.
        start_pos: Tuple (x, y) starting pixel position.
        config: Game configuration dictionary.
        wave_number: Current wave number for stat scaling.

    Returns:
        A new Enemy instance.
    """
    pass
