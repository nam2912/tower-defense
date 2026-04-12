"""Game configuration and constants.

get_config() returns one big dict of settings; the rest of the game reads that
dict from arguments instead of globals, so balancing mostly means editing here.
"""

from enums import TowerType, EnemyType


def _screen_config():
    """Return screen and grid settings."""
    return {
        "screen": {
            "width": 1200,
            "height": 800,
            "fps": 60,
            "title": "Tower Defense"
        },
        "grid": {
            "tile_size": 80,
            "cols": 15,
            "rows": 10
        },
    }


def _gameplay_config():
    """Return gameplay balance settings."""
    return {
        "gameplay": {
            "starting_gold": 400,
            "starting_lives": 1,
            "base_hp": 20,
            "base_upgrade_cost": [0, 150, 280, 450, 700],
            "base_upgrade_hp": [20, 28, 38, 50, 65],
            "base_upgrade_armor": [0, 1, 2, 3, 5],
            "round_bonus_gold": 65,
            "kill_gold_base": 13,
            "max_tower_level": 15,
            "free_build_slots": 8,
            "slot_unlock_cost": 60
        },
        "tower_unlocks": {
            TowerType.FORTRESS: 1,
            TowerType.ARCHER: 1,
            TowerType.BARRACKS: 1,
            TowerType.MAGE: 1,
            TowerType.ARTILLERY: 1,
            TowerType.FREEZE: 5,
            TowerType.POISON: 10,
            TowerType.BALLISTA: 15,
            TowerType.TESLA: 20,
            TowerType.NECROMANCER: 25,
            TowerType.LASER: 30,
        },
    }


def _tower_stats():
    """Return tower stat tables keyed by TowerType."""
    stats = _base_tower_stats()
    stats.update(_advanced_tower_stats())
    return stats


def _base_tower_stats():
    """Return stats for Fortress, Archer, Barracks, Mage, and Artillery."""
    return {
            TowerType.FORTRESS: {
                "cost": 40,
                "damage": [3, 4, 6, 8, 11, 15, 21, 29, 40, 55, 76, 105, 145, 200, 276],
                "attack_range": [1.5, 1.5, 1.6, 1.6, 1.7, 1.7, 1.8, 1.8, 1.9, 1.9, 2.0, 2.0, 2.1, 2.1, 2.2],
                "attack_speed": [2.0, 1.90, 1.80, 1.72, 1.64, 1.56, 1.48, 1.42, 1.36, 1.30, 1.24, 1.18, 1.12, 1.06, 1.00],
                "upgrade_cost": [0, 30, 50, 75, 110, 160, 225, 315, 440, 620, 870, 1220, 1710, 2395, 3355],
                "tower_hp": [120, 145, 175, 210, 255, 310, 375, 455, 550, 665, 805, 975, 1180, 1430, 1730],
                "tower_armor": [3, 4, 5, 6, 7, 8, 10, 12, 14, 16, 19, 22, 25, 29, 34],
                "description": "Tanky fortress, blocks bomber damage"
            },
            TowerType.ARCHER: {
                "cost": 50,
                "damage": [11, 15, 20, 27, 37, 50, 68, 93, 128, 176, 243, 335, 462, 641, 890],
                "attack_range": [3.2, 3.3, 3.4, 3.5, 3.7, 3.8, 3.9, 4.0, 4.2, 4.3, 4.5, 4.6, 4.8, 5.0, 5.2],
                "attack_speed": [0.85, 0.80, 0.75, 0.72, 0.68, 0.64, 0.60, 0.56, 0.52, 0.48, 0.44, 0.41, 0.38, 0.35, 0.32],
                "upgrade_cost": [0, 35, 55, 85, 125, 180, 255, 360, 505, 710, 995, 1395, 1955, 2740, 3835],
                "tower_hp": [40, 44, 48, 53, 58, 64, 70, 77, 85, 93, 102, 112, 123, 136, 150],
                "tower_armor": [0, 0, 0, 1, 1, 1, 2, 2, 2, 3, 3, 3, 4, 4, 5],
                "description": "Fast single-target damage"
            },
            TowerType.BARRACKS: {
                "cost": 70,
                "damage": [7, 10, 14, 19, 26, 35, 48, 65, 88, 120, 165, 225, 310, 428, 594],
                "attack_range": [1.5, 1.5, 1.5, 1.5, 1.5, 1.5, 1.5, 1.5, 1.5, 1.5, 1.5, 1.5, 1.5, 1.5, 1.5],
                "attack_speed": [0.85, 0.80, 0.76, 0.72, 0.68, 0.64, 0.60, 0.56, 0.52, 0.48, 0.44, 0.41, 0.38, 0.35, 0.32],
                "soldier_count": [3, 3, 3, 3, 4, 4, 4, 5, 5, 5, 6, 6, 6, 7, 7],
                "soldier_hp": [46, 62, 85, 115, 155, 210, 285, 390, 540, 755, 1060, 1485, 2080, 2910, 4075],
                "upgrade_cost": [0, 50, 80, 120, 175, 250, 355, 500, 700, 980, 1375, 1925, 2700, 3780, 5295],
                "tower_hp": [60, 66, 73, 80, 88, 97, 107, 118, 130, 143, 157, 173, 190, 209, 230],
                "tower_armor": [1, 1, 1, 2, 2, 2, 3, 3, 3, 4, 4, 5, 5, 6, 7],
                "description": "Soldiers block enemies on path"
            },
            TowerType.MAGE: {
                "cost": 100,
                "damage": [18, 25, 34, 46, 62, 84, 114, 156, 214, 300, 420, 588, 823, 1152, 1613],
                "attack_range": [2.8, 2.9, 3.0, 3.1, 3.2, 3.3, 3.4, 3.5, 3.6, 3.7, 3.9, 4.0, 4.2, 4.3, 4.5],
                "attack_speed": [1.3, 1.22, 1.14, 1.07, 1.00, 0.94, 0.88, 0.82, 0.77, 0.71, 0.65, 0.60, 0.55, 0.51, 0.47],
                "upgrade_cost": [0, 70, 110, 165, 245, 350, 500, 710, 1000, 1400, 1960, 2745, 3845, 5385, 7540],
                "ignore_armor": True,
                "tower_hp": [35, 38, 42, 46, 51, 56, 62, 68, 75, 82, 90, 99, 109, 120, 132],
                "tower_armor": [0, 0, 0, 0, 1, 1, 1, 2, 2, 2, 3, 3, 3, 4, 4],
                "description": "Magic damage, ignores armor"
            },
            TowerType.ARTILLERY: {
                "cost": 115,
                "damage": [29, 39, 52, 70, 95, 128, 175, 240, 334, 468, 655, 917, 1284, 1798, 2517],
                "attack_range": [3.2, 3.3, 3.4, 3.5, 3.7, 3.8, 3.9, 4.0, 4.1, 4.3, 4.4, 4.6, 4.7, 4.9, 5.0],
                "attack_speed": [2.2, 2.10, 2.00, 1.90, 1.80, 1.72, 1.64, 1.56, 1.50, 1.41, 1.32, 1.24, 1.16, 1.09, 1.02],
                "splash_radius": [1.0, 1.1, 1.2, 1.3, 1.4, 1.5, 1.6, 1.7, 1.8, 1.9, 2.0, 2.2, 2.4, 2.6, 2.8],
                "upgrade_cost": [0, 90, 140, 210, 310, 450, 640, 900, 1260, 1765, 2475, 3465, 4850, 6790, 9510],
                "tower_hp": [55, 60, 66, 73, 80, 88, 97, 107, 118, 130, 143, 157, 173, 190, 209],
                "tower_armor": [1, 1, 1, 2, 2, 2, 3, 3, 4, 4, 5, 5, 6, 6, 7],
                "description": "Slow AOE splash damage"
            },
        }


def _advanced_tower_stats():
    """Return stats for Freeze, Poison, Ballista, Tesla, Necromancer, Laser."""
    return {
            TowerType.FREEZE: {
                "cost": 120,
                "damage": [6, 9, 13, 18, 25, 35, 49, 69, 97, 135, 190, 266, 372, 521, 729],
                "attack_range": [2.5, 2.6, 2.7, 2.9, 3.0, 3.1, 3.3, 3.4, 3.6, 3.7, 3.9, 4.0, 4.2, 4.3, 4.5],
                "attack_speed": [2.0, 1.85, 1.72, 1.59, 1.48, 1.37, 1.27, 1.18, 1.10, 1.02, 0.95, 0.88, 0.82, 0.76, 0.70],
                "slow_factor": [0.50, 0.46, 0.42, 0.38, 0.35, 0.32, 0.29, 0.27, 0.25, 0.23, 0.21, 0.19, 0.17, 0.15, 0.13],
                "slow_duration": [1.5, 1.7, 1.9, 2.1, 2.3, 2.5, 2.7, 2.9, 3.1, 3.3, 3.5, 3.7, 4.0, 4.3, 4.6],
                "upgrade_cost": [0, 85, 130, 195, 285, 410, 585, 825, 1160, 1625, 2275, 3185, 4460, 6245, 8745],
                "tower_hp": [45, 49, 54, 59, 65, 72, 79, 87, 96, 105, 116, 128, 140, 154, 170],
                "tower_armor": [0, 0, 1, 1, 1, 2, 2, 2, 3, 3, 3, 4, 4, 5, 5],
                "description": "Slows enemies, unlocked at R5"
            },
            TowerType.POISON: {
                "cost": 130,
                "damage": [5, 7, 10, 14, 20, 28, 39, 55, 77, 108, 151, 211, 296, 414, 580],
                "attack_range": [3.0, 3.1, 3.2, 3.4, 3.5, 3.7, 3.8, 4.0, 4.1, 4.3, 4.4, 4.6, 4.7, 4.9, 5.0],
                "attack_speed": [2.0, 1.85, 1.72, 1.59, 1.48, 1.37, 1.27, 1.18, 1.10, 1.02, 0.95, 0.88, 0.82, 0.76, 0.70],
                "poison_dps": [10, 14, 20, 28, 39, 55, 77, 108, 151, 211, 296, 414, 580, 812, 1137],
                "poison_duration": [2.5, 2.7, 2.9, 3.1, 3.3, 3.5, 3.7, 3.9, 4.1, 4.3, 4.5, 4.8, 5.1, 5.4, 5.7],
                "upgrade_cost": [0, 90, 140, 210, 310, 450, 640, 900, 1260, 1765, 2475, 3465, 4850, 6790, 9510],
                "ignore_armor": True,
                "tower_hp": [45, 49, 54, 59, 65, 72, 79, 87, 96, 105, 116, 128, 140, 154, 170],
                "tower_armor": [0, 0, 1, 1, 1, 2, 2, 2, 3, 3, 3, 4, 4, 5, 5],
                "description": "Poison DOT, unlocked at R10"
            },
            TowerType.BALLISTA: {
                "cost": 150,
                "damage": [40, 56, 78, 110, 154, 216, 302, 423, 592, 829, 1161, 1625, 2275, 3185, 4460],
                "attack_range": [4.0, 4.1, 4.2, 4.3, 4.5, 4.6, 4.8, 4.9, 5.1, 5.2, 5.4, 5.5, 5.7, 5.8, 6.0],
                "attack_speed": [2.8, 2.60, 2.42, 2.25, 2.09, 1.95, 1.81, 1.69, 1.57, 1.46, 1.36, 1.27, 1.18, 1.10, 1.02],
                "upgrade_cost": [0, 105, 160, 240, 350, 505, 720, 1010, 1415, 1980, 2775, 3885, 5440, 7615, 10665],
                "pierce": [2, 2, 2, 3, 3, 3, 4, 4, 4, 5, 5, 5, 6, 6, 7],
                "tower_hp": [55, 60, 66, 73, 80, 88, 97, 107, 118, 130, 143, 157, 173, 190, 209],
                "tower_armor": [1, 1, 2, 2, 3, 3, 4, 4, 5, 5, 6, 6, 7, 7, 8],
                "description": "Long-range bolt, pierces (R15)"
            },
            TowerType.TESLA: {
                "cost": 180,
                "damage": [28, 39, 55, 77, 108, 151, 211, 296, 414, 580, 812, 1137, 1592, 2229, 3120],
                "attack_range": [2.8, 2.9, 3.0, 3.1, 3.3, 3.4, 3.5, 3.7, 3.8, 4.0, 4.1, 4.2, 4.4, 4.5, 4.7],
                "attack_speed": [1.8, 1.67, 1.55, 1.44, 1.34, 1.25, 1.16, 1.08, 1.00, 0.93, 0.87, 0.81, 0.75, 0.70, 0.65],
                "chain_count": [2, 2, 2, 3, 3, 3, 4, 4, 4, 5, 5, 5, 6, 6, 7],
                "chain_range": [1.5, 1.6, 1.6, 1.7, 1.7, 1.8, 1.8, 1.9, 2.0, 2.0, 2.1, 2.1, 2.2, 2.3, 2.4],
                "upgrade_cost": [0, 125, 190, 285, 420, 600, 855, 1210, 1700, 2380, 3335, 4670, 6540, 9155, 12820],
                "tower_hp": [50, 55, 60, 66, 73, 80, 88, 97, 107, 118, 130, 143, 157, 173, 190],
                "tower_armor": [0, 0, 1, 1, 2, 2, 3, 3, 4, 4, 5, 5, 6, 6, 7],
                "description": "Chain lightning, hits nearby (R20)"
            },
            TowerType.NECROMANCER: {
                "cost": 220,
                "damage": [20, 28, 39, 55, 77, 108, 151, 211, 296, 414, 580, 812, 1137, 1592, 2229],
                "attack_range": [3.0, 3.1, 3.2, 3.4, 3.5, 3.7, 3.8, 4.0, 4.1, 4.3, 4.4, 4.6, 4.7, 4.9, 5.0],
                "attack_speed": [2.5, 2.30, 2.12, 1.95, 1.80, 1.66, 1.53, 1.41, 1.30, 1.20, 1.10, 1.02, 0.94, 0.86, 0.80],
                "lifesteal": [0.12, 0.14, 0.16, 0.18, 0.20, 0.22, 0.24, 0.26, 0.28, 0.30, 0.33, 0.36, 0.39, 0.42, 0.45],
                "upgrade_cost": [0, 155, 235, 350, 520, 745, 1060, 1500, 2115, 2960, 4145, 5805, 8130, 11380, 15935],
                "ignore_armor": True,
                "tower_hp": [45, 49, 54, 59, 65, 72, 79, 87, 96, 105, 116, 128, 140, 154, 170],
                "tower_armor": [0, 0, 0, 1, 1, 1, 2, 2, 3, 3, 4, 4, 5, 5, 6],
                "description": "Lifesteal heals base (R25)"
            },
            TowerType.LASER: {
                "cost": 280,
                "damage": [38, 53, 74, 104, 146, 204, 286, 400, 560, 784, 1098, 1537, 2152, 3013, 4218],
                "attack_range": [4.0, 4.1, 4.2, 4.3, 4.5, 4.6, 4.8, 4.9, 5.1, 5.2, 5.4, 5.5, 5.7, 5.8, 6.0],
                "attack_speed": [3.0, 2.75, 2.53, 2.32, 2.13, 1.96, 1.80, 1.66, 1.52, 1.40, 1.29, 1.18, 1.09, 1.00, 0.92],
                "upgrade_cost": [0, 195, 295, 445, 665, 950, 1355, 1925, 2720, 3825, 5355, 7500, 10500, 14700, 20580],
                "ignore_armor": True,
                "tower_hp": [40, 44, 48, 53, 58, 64, 70, 77, 85, 93, 102, 112, 123, 136, 150],
                "tower_armor": [0, 0, 0, 0, 1, 1, 1, 2, 2, 3, 3, 4, 4, 5, 5],
                "description": "High damage beam (R30)"
            },
        }


def _enemy_stats():
    """Return enemy stat tables keyed by EnemyType."""
    return {
            EnemyType.GRUNT: {
                "hp": 80,
                "speed": 1.3,
                "armor": 0,
                "gold_reward": 7
            },
            EnemyType.RUNNER: {
                "hp": 45,
                "speed": 2.8,
                "armor": 0,
                "gold_reward": 5
            },
            EnemyType.ARMORED: {
                "hp": 200,
                "speed": 0.7,
                "armor": 8,
                "gold_reward": 13
            },
            EnemyType.BOMBER: {
                "hp": 120,
                "speed": 1.0,
                "armor": 2,
                "gold_reward": 16,
                "tower_damage": 3
            },
            EnemyType.BOSS: {
                "hp": 800,
                "speed": 0.5,
                "armor": 15,
                "gold_reward": 65
            }
        }


def _color_config():
    """Return UI colour palette."""
    return {
            "background": (34, 139, 34),
            "path": (139, 119, 101),
            "grid_line": (200, 200, 200),
            "build_spot": (100, 200, 100),
            "build_spot_hover": (150, 255, 150),
            "health_bar_bg": (255, 0, 0),
            "health_bar_fg": (0, 255, 0),
            "text": (255, 255, 255),
            "text_dark": (0, 0, 0),
            "gold": (255, 215, 0),
            "ui_bg": (40, 40, 40),
            "ui_border": (100, 100, 100),
            "button": (70, 130, 180),
            "button_hover": (100, 160, 210),
            "menu_bg": (20, 20, 40)
        }


def get_config():
    """Return the complete game configuration dictionary.

    Composes screen, gameplay, tower, enemy, and colour sub-configs
    into a single dict passed to every subsystem via constructor injection.

    Returns:
        dict: All game settings.
    """
    config = {}
    config.update(_screen_config())
    config.update(_gameplay_config())
    config["towers"] = _tower_stats()
    config["enemies"] = _enemy_stats()
    config["colors"] = _color_config()
    return config
