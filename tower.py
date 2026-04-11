"""Tower module.

Base Tower class with targeting, attacks, upgrades, and HP/armor.
Specialized tower subclasses live in ``tower_special.py``.

The ``create_tower`` factory picks the right subclass from the tower type
so stats and setup stay in one place.

Tower types (unlock round in parentheses):
- Fortress: tanky damage sponge, blocks bomber damage (R1)
- Archer: fast single-target (R1)
- Barracks: spawns soldiers that block enemies (R1)
- Mage: magic damage ignoring armor (R1)
- Artillery: AOE splash damage (R1)
- Freeze: slows enemies (R5)
- Poison: damage-over-time, ignores armor (R10)
- Ballista: long-range piercing bolts (R15)
- Tesla: chain lightning hitting nearby enemies (R20)
- Necromancer: lifesteal heals base, ignores armor (R25)
- Laser: high single-target beam, ignores armor (R30)
"""

import math
from enums import TowerType


class Tower:
    """A defensive tower that attacks enemies within range.

    Attributes:
        tower_type: TowerType enum value.
        x: Grid column position.
        y: Grid row position.
        pixel_x: Pixel x position (center of tile).
        pixel_y: Pixel y position (center of tile).
        level: Upgrade tier (1 to max_level).
        damage: Current damage per attack.
        attack_range: Current targeting radius in tiles.
        attack_speed: Current seconds between attacks.
        attack_cooldown: Time remaining until next attack.
        target: Currently targeted Enemy, or None.
        config: Tower type configuration from game config.
        tile_size: Size of tiles in pixels.
    """

    def __init__(self, tower_type, col, row, config, tile_size):
        """Initialize a tower.

        Args:
            tower_type: TowerType enum value.
            col: Grid column position.
            row: Grid row position.
            config: Tower configuration dict for this tower type.
            tile_size: Size of tiles in pixels.
        """
        self.tower_type = tower_type
        self.x = col
        self.y = row
        self.tile_size = tile_size
        self.pixel_x = col * tile_size + tile_size // 2
        self.pixel_y = row * tile_size + tile_size // 2
        self.level = 1
        self.config = config
        self.max_level = len(config["damage"])
        self.damage = config["damage"][0]
        self.attack_range = config["attack_range"][0]
        self.attack_speed = config["attack_speed"][0]
        self.attack_cooldown = 0.0
        self.target = None
        base_hp = (config.get("tower_hp", [50])[0]
                   if "tower_hp" in config else 50)
        self.tower_hp = base_hp
        self.tower_max_hp = base_hp
        self.tower_armor = (config.get("tower_armor", [0])[0]
                            if "tower_armor" in config else 0)
        self.is_destroyed = False

    def update(self, enemies, dt):
        """Update tower state: find target and attack.

        Args:
            enemies: List of active Enemy instances.
            dt: Delta time in seconds.

        Returns:
            List of enemies killed this frame.
        """
        killed = []
        self.attack_cooldown -= dt

        if self.target is None or not self.target.is_alive:
            self.target = self.find_target(enemies)

        if self.target is not None and not self._is_in_range(self.target):
            self.target = self.find_target(enemies)

        if self.target is not None and self.attack_cooldown <= 0:
            killed_enemies = self.attack(enemies)
            killed.extend(killed_enemies)
            self.attack_cooldown = self.attack_speed

        return killed

    def find_target(self, enemies):
        """Find the closest enemy within attack range."""
        closest = None
        closest_dist = self._get_range_pixels()

        for enemy in enemies:
            if not enemy.is_alive:
                continue
            dist = self._distance_to(enemy)
            if dist < closest_dist:
                closest_dist = dist
                closest = enemy

        return closest

    def attack(self, enemies):
        """Attack the current target."""
        killed = []
        if self.target is None or not self.target.is_alive:
            return killed

        ignore_armor = self.config.get("ignore_armor", False)
        died = self.target.take_damage(self.damage, ignore_armor)
        if died:
            killed.append(self.target)
            self.target = None

        return killed

    def upgrade(self):
        """Upgrade the tower to the next level.

        Returns:
            True if upgrade was successful.
        """
        if self.level >= self.max_level:
            return False

        self.level += 1
        idx = self.level - 1
        self.damage = self.config["damage"][idx]
        self.attack_range = self.config["attack_range"][idx]
        self.attack_speed = self.config["attack_speed"][idx]
        if "tower_hp" in self.config:
            self.tower_max_hp = self.config["tower_hp"][idx]
            self.tower_hp = self.tower_max_hp
        if "tower_armor" in self.config:
            self.tower_armor = self.config["tower_armor"][idx]
        return True

    def get_upgrade_cost(self):
        """Get the cost to upgrade to the next level."""
        if self.level >= self.max_level:
            return 0
        return self.config["upgrade_cost"][self.level]

    def get_sell_value(self):
        """Get the gold refund for selling this tower (60% of total)."""
        total_spent = self.config["cost"]
        for i in range(1, self.level):
            total_spent += self.config["upgrade_cost"][i]
        return int(total_spent * 0.6)

    def _distance_to(self, enemy):
        """Calculate pixel distance to an enemy."""
        dx = enemy.x - self.pixel_x
        dy = enemy.y - self.pixel_y
        return math.sqrt(dx * dx + dy * dy)

    def _is_in_range(self, enemy):
        """Check if an enemy is within attack range."""
        return self._distance_to(enemy) <= self._get_range_pixels()

    def take_tower_damage(self, damage):
        """Apply damage to this tower from bomber enemies, reduced by armor.

        Args:
            damage: Raw damage amount.

        Returns:
            True if the tower was destroyed.
        """
        actual = max(1, damage - self.tower_armor)
        self.tower_hp -= actual
        if self.tower_hp <= 0:
            self.tower_hp = 0
            self.is_destroyed = True
            return True
        return False

    def get_tower_hp_ratio(self):
        """Get tower HP as a ratio."""
        if self.tower_max_hp <= 0:
            return 0.0
        return self.tower_hp / self.tower_max_hp

    def _get_range_pixels(self):
        """Convert tile-based range to pixel range."""
        return self.attack_range * self.tile_size


# Re-export subclasses so existing imports work unchanged.
from tower_special import (  # noqa: E402, F401
    FortressTower,
    ArtilleryTower,
    BarracksTower,
    FreezeTower,
    PoisonTower,
    BallistaTower,
    TeslaTower,
    NecromancerTower,
    LaserTower,
)


def create_tower(tower_type, col, row, config, tile_size, game_map=None):
    """Factory function to create the appropriate tower subclass.

    Args:
        tower_type: TowerType enum value.
        col: Grid column position.
        row: Grid row position.
        config: Full game configuration dictionary.
        tile_size: Size of tiles in pixels.
        game_map: Optional GameMap for towers that need path info.

    Returns:
        A Tower instance of the appropriate subclass.
    """
    tower_config = config["towers"][tower_type]

    if tower_type == TowerType.FORTRESS:
        return FortressTower(col, row, tower_config, tile_size)
    elif tower_type == TowerType.ARTILLERY:
        return ArtilleryTower(col, row, tower_config, tile_size)
    elif tower_type == TowerType.BARRACKS:
        return BarracksTower(col, row, tower_config, tile_size, game_map)
    elif tower_type == TowerType.FREEZE:
        return FreezeTower(col, row, tower_config, tile_size)
    elif tower_type == TowerType.BALLISTA:
        return BallistaTower(col, row, tower_config, tile_size)
    elif tower_type == TowerType.POISON:
        return PoisonTower(col, row, tower_config, tile_size)
    elif tower_type == TowerType.TESLA:
        return TeslaTower(col, row, tower_config, tile_size)
    elif tower_type == TowerType.NECROMANCER:
        return NecromancerTower(col, row, tower_config, tile_size)
    elif tower_type == TowerType.LASER:
        return LaserTower(col, row, tower_config, tile_size)
    else:
        return Tower(tower_type, col, row, tower_config, tile_size)
