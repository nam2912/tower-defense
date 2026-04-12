"""Enemy module.

Enemy class plus a factory-style function that spawns the right enemy type
with HP and stats scaled to the current wave.
"""

import math


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
        self.enemy_type = enemy_type
        self.x = float(x)
        self.y = float(y)
        self.hp = hp
        self.max_hp = hp
        self.speed = speed
        self.armor = armor
        self.path_index = 1
        self.is_alive = True
        self.gold_reward = gold_reward
        self.hit_timer = 0.0
        self.direction_x = 1.0
        self.direction_y = 0.0
        self.blocked_by = None
        self.attack_cooldown = 0.0
        self.attack_damage = max(5, int(hp * 0.05))
        self.base_speed = speed
        self.slow_timer = 0.0
        self.slow_factor = 1.0
        self.poison_timer = 0.0
        self.poison_dps = 0
        self.tower_damage = 0
        self.bomb_cooldown = 0.0
        self.bomb_interval = 3.0

    def move(self, path_waypoints, dt=0.016):
        """Move the enemy toward the next waypoint.

        If blocked by a soldier, the enemy stops and fights
        the soldier instead of advancing.

        Args:
            path_waypoints: List of (x, y) pixel waypoints.
            dt: Delta time in seconds.

        Returns:
            True if the enemy reached the final waypoint (base).
        """
        if self.blocked_by is not None:
            if not self.blocked_by.is_alive:
                self.blocked_by = None
            else:
                self._fight_blocker(dt)
                return False

        if self.path_index >= len(path_waypoints):
            return True

        target_x, target_y = path_waypoints[self.path_index]
        dx = target_x - self.x
        dy = target_y - self.y
        distance = math.sqrt(dx * dx + dy * dy)

        if distance < self.speed:
            self.x = float(target_x)
            self.y = float(target_y)
            self.path_index += 1
            if self.path_index >= len(path_waypoints):
                return True
        else:
            self.direction_x = dx / distance
            self.direction_y = dy / distance
            self.x += self.direction_x * self.speed
            self.y += self.direction_y * self.speed

        return False

    def _fight_blocker(self, dt):
        """Attack the soldier that is blocking this enemy.

        Args:
            dt: Delta time in seconds.
        """
        if self.blocked_by is None or not self.blocked_by.is_alive:
            self.blocked_by = None
            return
        self.attack_cooldown -= dt
        if self.attack_cooldown <= 0:
            self.blocked_by.take_damage(self.attack_damage)
            self.attack_cooldown = 1.0
            if self.blocked_by is None or not self.blocked_by.is_alive:
                self.blocked_by = None

    def take_damage(self, damage, ignore_armor=False):
        """Apply damage to this enemy, accounting for armor.

        Args:
            damage: Raw damage amount.
            ignore_armor: If True, bypass armor reduction.

        Returns:
            True if the enemy died from this damage.
        """
        if not self.is_alive:
            return False

        actual_damage = damage
        if not ignore_armor:
            actual_damage = max(1, damage - self.armor)

        self.hp -= actual_damage
        self.hit_timer = 0.15
        if self.hp <= 0:
            self.hp = 0
            self.is_alive = False
            return True
        return False

    def apply_slow(self, factor, duration):
        """Apply a slow debuff to this enemy.

        Args:
            factor: Speed multiplier (0.0-1.0, lower = slower).
            duration: How long the slow lasts in seconds.
        """
        if factor < self.slow_factor or self.slow_timer <= 0:
            self.slow_factor = factor
            self.slow_timer = duration

    def apply_poison(self, dps, duration):
        """Apply a poison DOT debuff to this enemy.

        Args:
            dps: Damage per second from poison.
            duration: How long the poison lasts in seconds.
        """
        self.poison_dps = max(self.poison_dps, dps)
        self.poison_timer = max(self.poison_timer, duration)

    def update_timers(self, dt):
        """Decrement animation timers and apply debuff effects.

        Args:
            dt: Delta time in seconds.
        """
        if self.hit_timer > 0:
            self.hit_timer -= dt

        if self.slow_timer > 0:
            self.slow_timer -= dt
            self.speed = self.base_speed * self.slow_factor
            if self.slow_timer <= 0:
                self.speed = self.base_speed
                self.slow_factor = 1.0
        else:
            self.speed = self.base_speed

        if self.poison_timer > 0:
            self.poison_timer -= dt
            poison_damage = self.poison_dps * dt
            self.hp -= poison_damage
            if self.hp <= 0:
                self.hp = 0
                self.is_alive = False
            if self.poison_timer <= 0:
                self.poison_dps = 0

    def get_hp_ratio(self):
        """Get the current HP as a ratio of max HP.

        Returns:
            Float between 0.0 and 1.0.
        """
        if self.max_hp <= 0:
            return 0.0
        return self.hp / self.max_hp


def create_enemy(enemy_type, start_pos, config, round_number):
    """Factory function to create an enemy with round-scaled stats.

    Uses exponential scaling so enemies stay challenging even with
    upgraded towers:
    - HP scales by 1.15^(round-1) — doubles roughly every 5 rounds.
    - Speed scales by +2% per round (capped at 1.8x).
    - Armor gains +0.5 per round.
    - Gold reward scales by +3% per round.

    Args:
        enemy_type: EnemyType enum value.
        start_pos: Tuple (x, y) starting pixel position.
        config: Game configuration dictionary.
        round_number: Current round number for stat scaling.

    Returns:
        A new Enemy instance.
    """
    base = config["enemies"][enemy_type]
    r = round_number

    hp_scale = 1.15 ** (r - 1)
    speed_scale = min(1.0 + (r - 1) * 0.02, 1.8)
    armor_extra = int((r - 1) * 0.5)
    gold_scale = 1.0 + (r - 1) * 0.03

    hp = int(base["hp"] * hp_scale)
    speed = base["speed"] * speed_scale
    armor = base["armor"] + armor_extra
    gold_reward = int(base["gold_reward"] * gold_scale)

    enemy = Enemy(
        enemy_type=enemy_type,
        x=start_pos[0],
        y=start_pos[1],
        hp=hp,
        speed=speed,
        armor=armor,
        gold_reward=gold_reward
    )
    if "tower_damage" in base:
        enemy.tower_damage = int(base["tower_damage"] * (1.0 + (r - 1) * 0.1))
    return enemy
