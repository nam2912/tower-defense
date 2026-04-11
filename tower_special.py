"""Specialized tower subclasses.

Each subclass extends the base :class:`Tower` with unique mechanics:
AOE splash, soldier spawning, debuffs, piercing, chain lightning,
lifesteal, and beams.
"""

import math
from enums import TowerType
from soldier import Soldier
from tower import Tower


class FortressTower(Tower):
    """Heavily armored defensive tower designed to absorb bomber attacks.

    Has the highest HP and armor of all towers but deals minimal damage.
    Acts as a damage sponge to shield nearby valuable towers.
    """

    def __init__(self, col, row, config, tile_size):
        """Initialize a fortress tower."""
        super().__init__(TowerType.FORTRESS, col, row, config, tile_size)

    def take_tower_damage(self, damage):
        """Apply damage to fortress, with extra armor effectiveness.

        Fortress towers reduce incoming damage more heavily than
        standard towers due to their reinforced construction.

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


class ArtilleryTower(Tower):
    """Tower with area-of-effect splash damage."""

    def __init__(self, col, row, config, tile_size):
        """Initialize an artillery tower with splash radius."""
        super().__init__(TowerType.ARTILLERY, col, row, config, tile_size)
        self.splash_radius = config["splash_radius"][0]

    def attack(self, enemies):
        """Deal splash damage to all enemies near the target."""
        killed = []
        if self.target is None or not self.target.is_alive:
            return killed

        splash_pixels = self.splash_radius * self.tile_size
        for enemy in enemies:
            if not enemy.is_alive:
                continue
            dx = enemy.x - self.target.x
            dy = enemy.y - self.target.y
            dist = math.sqrt(dx * dx + dy * dy)
            if dist <= splash_pixels:
                died = enemy.take_damage(self.damage)
                if died:
                    killed.append(enemy)

        if not self.target.is_alive:
            self.target = None
        return killed

    def upgrade(self):
        """Upgrade artillery, increasing splash radius."""
        result = super().upgrade()
        if result:
            self.splash_radius = self.config["splash_radius"][
                self.level - 1]
        return result


class BarracksTower(Tower):
    """Tower that spawns soldier units for melee combat.

    Soldiers block enemies on the path, preventing them
    from advancing until the soldier is killed. Rally points
    are placed on adjacent path tiles so soldiers actually
    intercept enemies.
    """

    def __init__(self, col, row, config, tile_size, game_map=None):
        """Initialize barracks with soldiers on adjacent path tiles."""
        super().__init__(TowerType.BARRACKS, col, row, config, tile_size)
        self.soldiers = []
        self.max_soldiers = config["soldier_count"][0]
        self.soldier_hp = config["soldier_hp"][0]
        self.respawn_timer = 0.0
        self.respawn_delay = 5.0
        self.game_map = game_map
        self._path_rally_points = self._compute_path_rally_points()
        self._spawn_initial_soldiers()

    def _compute_path_rally_points(self):
        """Find pixel positions on adjacent path tiles for soldier rally.

        Returns:
            List of (px, py) pixel positions on nearby path tiles.
        """
        if self.game_map is None:
            return [(self.pixel_x, self.pixel_y)]

        col, row = self.x, self.y
        ts = self.tile_size
        path_positions = []
        for dc, dr in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            nc, nr = col + dc, row + dr
            if self.game_map.is_path_tile(nc, nr):
                px = nc * ts + ts // 2
                py = nr * ts + ts // 2
                path_positions.append((px, py))

        if not path_positions:
            return [(self.pixel_x, self.pixel_y)]
        return path_positions

    def _spawn_initial_soldiers(self):
        """Spawn the initial set of soldiers at rally positions."""
        for i in range(self.max_soldiers):
            rally = self._get_rally_point(i)
            soldier = Soldier(
                hp=self.soldier_hp,
                damage=self.damage,
                attack_speed=self.attack_speed,
                rally_point=rally
            )
            self.soldiers.append(soldier)

    def _get_rally_point(self, soldier_index):
        """Distribute soldiers across path tiles with small offsets."""
        path_pts = self._path_rally_points
        base_pt = path_pts[soldier_index % len(path_pts)]
        spread_offsets = [
            (0, 0), (-12, -12), (12, -12), (-12, 12), (12, 12),
            (0, -16), (0, 16), (-16, 0), (16, 0),
        ]
        offset_idx = soldier_index // len(path_pts)
        ox, oy = spread_offsets[offset_idx % len(spread_offsets)]
        return (base_pt[0] + ox, base_pt[1] + oy)

    def update(self, enemies, dt):
        """Update all soldiers and respawn dead ones after a delay."""
        killed = []
        for soldier in self.soldiers:
            soldier.update(enemies, dt)
        self.soldiers = [s for s in self.soldiers if s.is_alive]

        if len(self.soldiers) < self.max_soldiers:
            self.respawn_timer -= dt
            if self.respawn_timer <= 0:
                rally = self._get_rally_point(len(self.soldiers))
                new_soldier = Soldier(
                    hp=self.soldier_hp,
                    damage=self.damage,
                    attack_speed=self.attack_speed,
                    rally_point=rally
                )
                self.soldiers.append(new_soldier)
                self.respawn_timer = self.respawn_delay

        return killed

    def upgrade(self):
        """Upgrade barracks, increasing soldier count and HP."""
        result = super().upgrade()
        if result:
            idx = self.level - 1
            self.max_soldiers = self.config["soldier_count"][idx]
            self.soldier_hp = self.config["soldier_hp"][idx]
        return result

    def get_all_soldiers(self):
        """Return all living soldiers from this barracks."""
        return [s for s in self.soldiers if s.is_alive]


class FreezeTower(Tower):
    """Tower that slows enemies within range."""

    def __init__(self, col, row, config, tile_size):
        """Initialize freeze tower with slow factor and duration."""
        super().__init__(TowerType.FREEZE, col, row, config, tile_size)
        self.slow_factor = config["slow_factor"][0]
        self.slow_duration = config["slow_duration"][0]

    def attack(self, enemies):
        """Deal damage and apply slow debuff to the target."""
        killed = []
        if self.target is None or not self.target.is_alive:
            return killed

        died = self.target.take_damage(self.damage)
        self.target.apply_slow(self.slow_factor, self.slow_duration)
        if died:
            killed.append(self.target)
            self.target = None
        return killed

    def upgrade(self):
        """Upgrade freeze tower, improving slow factor and duration."""
        result = super().upgrade()
        if result:
            idx = self.level - 1
            self.slow_factor = self.config["slow_factor"][idx]
            self.slow_duration = self.config["slow_duration"][idx]
        return result


class PoisonTower(Tower):
    """Tower that applies poison DOT to enemies."""

    def __init__(self, col, row, config, tile_size):
        """Initialize poison tower with DOT parameters."""
        super().__init__(TowerType.POISON, col, row, config, tile_size)
        self.poison_dps = config["poison_dps"][0]
        self.poison_duration = config["poison_duration"][0]

    def attack(self, enemies):
        """Deal damage and apply poison DOT to the target."""
        killed = []
        if self.target is None or not self.target.is_alive:
            return killed

        ignore_armor = self.config.get("ignore_armor", False)
        died = self.target.take_damage(self.damage, ignore_armor)
        self.target.apply_poison(self.poison_dps, self.poison_duration)
        if died:
            killed.append(self.target)
            self.target = None
        return killed

    def upgrade(self):
        """Upgrade poison tower, increasing DPS and duration."""
        result = super().upgrade()
        if result:
            idx = self.level - 1
            self.poison_dps = self.config["poison_dps"][idx]
            self.poison_duration = self.config["poison_duration"][idx]
        return result


class BallistaTower(Tower):
    """Long-range tower that pierces through multiple enemies."""

    def __init__(self, col, row, config, tile_size):
        """Initialize ballista tower with pierce count."""
        super().__init__(TowerType.BALLISTA, col, row, config, tile_size)
        self.pierce = config["pierce"][0]

    def attack(self, enemies):
        """Fire a piercing bolt that hits multiple enemies in a line."""
        killed = []
        if self.target is None or not self.target.is_alive:
            return killed

        hit_count = 0
        dx = self.target.x - self.pixel_x
        dy = self.target.y - self.pixel_y
        dist = math.sqrt(dx * dx + dy * dy)
        if dist == 0:
            return killed
        ndx, ndy = dx / dist, dy / dist

        sorted_enemies = sorted(
            [e for e in enemies if e.is_alive],
            key=lambda e: ((e.x - self.pixel_x) * ndx
                           + (e.y - self.pixel_y) * ndy)
        )
        for enemy in sorted_enemies:
            if hit_count >= self.pierce:
                break
            perp_dist = abs(
                (enemy.x - self.pixel_x) * (-ndy)
                + (enemy.y - self.pixel_y) * ndx
            )
            if (perp_dist < self.tile_size * 0.6
                    and self._is_in_range(enemy)):
                died = enemy.take_damage(self.damage)
                hit_count += 1
                if died:
                    killed.append(enemy)

        if self.target is not None and not self.target.is_alive:
            self.target = None
        return killed

    def upgrade(self):
        """Upgrade ballista, increasing pierce count."""
        result = super().upgrade()
        if result:
            self.pierce = self.config["pierce"][self.level - 1]
        return result


class TeslaTower(Tower):
    """Tower that fires chain lightning hitting nearby enemies."""

    def __init__(self, col, row, config, tile_size):
        """Initialize tesla tower with chain count and range."""
        super().__init__(TowerType.TESLA, col, row, config, tile_size)
        self.chain_count = config["chain_count"][0]
        self.chain_range = config["chain_range"][0]

    def attack(self, enemies):
        """Fire chain lightning that arcs between nearby enemies."""
        killed = []
        if self.target is None or not self.target.is_alive:
            return killed

        chain_pixels = self.chain_range * self.tile_size
        chained = set()
        current = self.target

        for _ in range(self.chain_count):
            if current is None or not current.is_alive:
                break
            if id(current) in chained:
                break
            chained.add(id(current))
            died = current.take_damage(self.damage)
            if died:
                killed.append(current)

            nearest = None
            nearest_dist = chain_pixels
            for enemy in enemies:
                if not enemy.is_alive or id(enemy) in chained:
                    continue
                edx = enemy.x - current.x
                edy = enemy.y - current.y
                edist = math.sqrt(edx * edx + edy * edy)
                if edist < nearest_dist:
                    nearest_dist = edist
                    nearest = enemy
            current = nearest

        if self.target is not None and not self.target.is_alive:
            self.target = None
        return killed

    def upgrade(self):
        """Upgrade tesla, increasing chain count and range."""
        result = super().upgrade()
        if result:
            idx = self.level - 1
            self.chain_count = self.config["chain_count"][idx]
            self.chain_range = self.config["chain_range"][idx]
        return result


class NecromancerTower(Tower):
    """Tower that steals life from enemies to heal the base."""

    def __init__(self, col, row, config, tile_size):
        """Initialize necromancer tower with lifesteal ratio."""
        super().__init__(TowerType.NECROMANCER, col, row, config, tile_size)
        self.lifesteal = config["lifesteal"][0]
        self.heal_accumulator = 0.0

    def attack(self, enemies):
        """Deal armor-ignoring damage and accumulate lifesteal heal."""
        killed = []
        if self.target is None or not self.target.is_alive:
            return killed

        ignore_armor = self.config.get("ignore_armor", False)
        died = self.target.take_damage(self.damage, ignore_armor)
        self.heal_accumulator += self.damage * self.lifesteal
        if died:
            killed.append(self.target)
            self.target = None
        return killed

    def get_pending_heal(self):
        """Retrieve and reset accumulated heal amount."""
        heal = int(self.heal_accumulator)
        self.heal_accumulator -= heal
        return heal

    def upgrade(self):
        """Upgrade necromancer, increasing lifesteal ratio."""
        result = super().upgrade()
        if result:
            self.lifesteal = self.config["lifesteal"][self.level - 1]
        return result


class LaserTower(Tower):
    """High-damage beam tower that ignores armor."""

    def __init__(self, col, row, config, tile_size):
        """Initialize laser tower with armor-ignoring beam attack."""
        super().__init__(TowerType.LASER, col, row, config, tile_size)
