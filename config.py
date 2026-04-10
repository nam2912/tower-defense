"""Game configuration and constants.

All game settings are stored in a dictionary returned by get_config().
No global variables — config is passed through function parameters.

Design patterns: Data-Driven Design, Dependency Injection.
See REFERENCES.md for full citations.
"""

from enums import TowerType, EnemyType


def get_config():
    """Return the complete game configuration dictionary.

    Returns:
        dict: All game settings including screen, gameplay, tower stats,
              enemy stats, and wave definitions.
    """
    pass
