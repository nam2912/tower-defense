"""Soldier module.

Soldier units spawned by Barracks towers. Each soldier has states:
idle -> moving -> fighting -> dying.

Soldiers block enemies on the path. When a soldier engages an enemy,
the enemy stops advancing and fights the soldier instead.
"""

import math
from enums import SoldierState


class Soldier:
    """A melee soldier unit spawned by a Barracks tower.

    Attributes:
        hp: Current health points.
        max_hp: Maximum health points.
        damage: Melee damage per attack.
        state: Current SoldierState.
        rally_point: Tuple (x, y) position to stand when idle.
        x: Current x pixel position.
        y: Current y pixel position.
        target: Currently engaged enemy, or None.
        attack_cooldown: Time until next attack.
        attack_speed: Seconds between attacks.
        move_speed: Movement speed in pixels per frame.
        is_alive: Whether the soldier is still active.
        engage_range: Detection range for nearby enemies.
    """

    def __init__(self, hp, damage, attack_speed, rally_point):
        """Initialize a soldier unit.

        Args:
            hp: Health points.
            damage: Melee damage per attack.
            attack_speed: Seconds between attacks.
            rally_point: Tuple (x, y) pixel position to stand when idle.
        """
        self.hp = hp
        self.max_hp = hp
        self.damage = damage
        self.state = SoldierState.IDLE
        self.rally_point = rally_point
        self.x = float(rally_point[0])
        self.y = float(rally_point[1])
        self.target = None
        self.attack_cooldown = 0.0
        self.attack_speed = attack_speed
        self.move_speed = 2.5
        self.is_alive = True
        self.engage_range = 80.0
        self.heal_rate = hp * 0.05

    def update(self, enemies, dt):
        """Update soldier state each frame.

        Args:
            enemies: List of active Enemy instances.
            dt: Delta time in seconds since last frame.
        """
        if not self.is_alive:
            return

        if self.state == SoldierState.IDLE:
            self._handle_idle(enemies, dt)
        elif self.state == SoldierState.MOVING:
            self._handle_moving(dt)
        elif self.state == SoldierState.FIGHTING:
            self._handle_fighting(enemies, dt)
        elif self.state == SoldierState.DYING:
            self._handle_dying()

    def _handle_idle(self, enemies, dt):
        """Look for nearby enemies. If none found, walk back and heal."""
        closest = self._find_closest_unblocked_enemy(enemies)
        if closest is not None:
            self.target = closest
            self.target.blocked_by = self
            self.state = SoldierState.MOVING
        else:
            any_alive = any(e.is_alive for e in enemies)
            self._return_to_rally(fast=not any_alive)
            if self.hp < self.max_hp:
                self.hp = min(self.max_hp, self.hp + self.heal_rate * dt)

    def _handle_moving(self, dt):
        """Move toward the target enemy to engage in melee.

        Args:
            dt: Delta time in seconds.
        """
        if self.target is None or not self.target.is_alive:
            self._release_target()
            self.state = SoldierState.IDLE
            return

        dx = self.target.x - self.x
        dy = self.target.y - self.y
        distance = math.sqrt(dx * dx + dy * dy)

        melee_range = 20.0
        if distance <= melee_range:
            self.state = SoldierState.FIGHTING
            return

        if distance > 0:
            direction_x = dx / distance
            direction_y = dy / distance
            self.x += direction_x * self.move_speed
            self.y += direction_y * self.move_speed

    def _handle_fighting(self, enemies, dt):
        """Attack the blocked enemy in melee.

        Args:
            enemies: List of active Enemy instances.
            dt: Delta time in seconds.
        """
        if self.target is None or not self.target.is_alive:
            self._release_target()
            self.state = SoldierState.IDLE
            return

        dx = self.target.x - self.x
        dy = self.target.y - self.y
        distance = math.sqrt(dx * dx + dy * dy)
        if distance > 35.0:
            self.state = SoldierState.MOVING
            return

        self.attack_cooldown -= dt
        if self.attack_cooldown <= 0:
            self.target.take_damage(self.damage)
            self.attack_cooldown = self.attack_speed
            if not self.target.is_alive:
                self._release_target()
                self.state = SoldierState.IDLE

    def _handle_dying(self):
        """Process death state — release any blocked enemy."""
        self._release_target()
        self.is_alive = False

    def _release_target(self):
        """Release the enemy from being blocked by this soldier."""
        if self.target is not None and hasattr(self.target, 'blocked_by'):
            if self.target.blocked_by is self:
                self.target.blocked_by = None
        self.target = None

    def take_damage(self, damage):
        """Receive damage from an enemy.

        Args:
            damage: Amount of damage to take.

        Returns:
            True if the soldier died.
        """
        self.hp -= damage
        if self.hp <= 0:
            self.hp = 0
            self.state = SoldierState.DYING
            self._release_target()
            self.is_alive = False
            return True
        return False

    def _find_closest_unblocked_enemy(self, enemies):
        """Find the closest living enemy within range not already blocked.

        Args:
            enemies: List of Enemy instances.

        Returns:
            The closest unblocked Enemy within range, or None.
        """
        closest = None
        closest_dist = self.engage_range

        for enemy in enemies:
            if not enemy.is_alive:
                continue
            if enemy.blocked_by is not None:
                continue
            dx = enemy.x - self.rally_point[0]
            dy = enemy.y - self.rally_point[1]
            dist = math.sqrt(dx * dx + dy * dy)
            if dist < closest_dist:
                closest_dist = dist
                closest = enemy

        return closest

    def _return_to_rally(self, fast=False):
        """Move soldier back toward rally point when no enemies.

        Args:
            fast: If True, move at full speed (used when wave is clear).
        """
        dx = self.rally_point[0] - self.x
        dy = self.rally_point[1] - self.y
        distance = math.sqrt(dx * dx + dy * dy)
        if distance > 3.0:
            speed_mult = 1.0 if fast else 0.5
            direction_x = dx / distance
            direction_y = dy / distance
            self.x += direction_x * self.move_speed * speed_mult
            self.y += direction_y * self.move_speed * speed_mult

    def return_to_rally(self, fast=False):
        """Public method: move soldier back to rally point.

        Args:
            fast: If True, move at full speed.
        """
        self._return_to_rally(fast=fast)

    def get_hp_ratio(self):
        """Get the current HP as a ratio of max HP.

        Returns:
            Float between 0.0 and 1.0.
        """
        if self.max_hp <= 0:
            return 0.0
        return self.hp / self.max_hp
