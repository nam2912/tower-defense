"""Game manager module.

Tracks game state (menu, playing, round complete, round failed, game over) and
updates all entities each frame. This is the main hub that ties gameplay together.

Kingdom Rush-style flow:
- Base has HP; enemies deal damage when they reach the end.
- Losing all base HP fails the round — player retries the same round.
- Clearing all enemies completes the round — player proceeds to next.
- Towers persist between rounds; enemies and projectiles reset.
- Rounds are infinite with progressive scaling.
"""

import math
import pygame
from enums import GameState, TowerType, EnemyType
from game_map import GameMap
from wave_manager import WaveManager
from tower import BarracksTower, NecromancerTower, ArtilleryTower
from renderer import Renderer
from game_input import GameInputMixin


class GameManager(GameInputMixin):
    """Central game state controller and entity coordinator.

    Attributes:
        config: Game configuration dictionary.
        state: Current GameState.
        game_map: GameMap instance.
        wave_manager: WaveManager instance.
        renderer: Renderer instance.
        towers: List of placed Tower instances.
        enemies: List of active Enemy instances.
        projectiles: List of visual projectile dicts.
        gold: Current player gold.
        base_hp: Current base health points.
        base_max_hp: Maximum base health points.
        current_round: Current round number.
        selected_tower_type: TowerType selected for placement, or None.
        selected_tower: Tower selected for info/upgrade, or None.
        highest_round: Highest round reached (for display).
    """

    def __init__(self, screen, config):
        """Initialize the game manager.

        Args:
            screen: Pygame display surface.
            config: Game configuration dictionary.
        """
        self.config = config
        self.state = GameState.MENU
        self.game_map = GameMap(config)
        self.wave_manager = WaveManager(config)
        self.renderer = Renderer(screen, config)
        self.towers = []
        self.enemies = []
        self.projectiles = []
        self.gold = config["gameplay"]["starting_gold"]
        self.base_level = 1
        self.base_max_hp = config["gameplay"]["base_upgrade_hp"][0]
        self.base_hp = self.base_max_hp
        self.current_round = 0
        self.highest_round = 0
        self.selected_tower_type = None
        self.selected_tower = None
        self.selected_base = False
        self.selected_build_spot = None
        self.round_timer = 0.0
        self.game_speed = 1
        self.base_armor = config["gameplay"]["base_upgrade_armor"][0]
        self.debug_mode = False
        self.music_volume = 0.3
        self.music_muted = False
        self.wave_countdown = 0.0
        self.wave_countdown_max = 60.0
        self.prep_phase = False
        self.moving_tower = None
        waypoints = self.game_map.get_path_pixel_waypoints()
        self.base_wp = waypoints[-1] if waypoints else None

    # ------------------------------------------------------------------
    # Update loop
    # ------------------------------------------------------------------

    def update(self, dt):
        """Update all game entities for one frame.

        Args:
            dt: Delta time in seconds since last frame.
        """
        if self.state != GameState.PLAYING:
            return

        if self.prep_phase:
            self.wave_countdown -= dt
            if self.wave_countdown <= 0:
                self._begin_next_round()
            return

        dt *= self.game_speed
        self.round_timer += dt

        path_waypoints = self.game_map.get_path_pixel_waypoints()
        start_pos = path_waypoints[0] if path_waypoints else (0, 0)
        self.wave_manager.update(self.enemies, start_pos, dt)

        for enemy in self.enemies:
            if not enemy.is_alive:
                continue
            reached_base = enemy.move(path_waypoints, dt)
            if reached_base:
                enemy.is_alive = False
                damage = self._get_enemy_base_damage(enemy)
                self.base_hp -= damage
                if self.base_hp <= 0:
                    self.base_hp = 0
                    self.state = GameState.ROUND_FAILED
                    return

        for enemy in self.enemies:
            enemy.update_timers(dt)

        self._process_bomber_attacks(dt)
        self._remove_destroyed_towers()

        for tower in self.towers:
            killed = tower.update(self.enemies, dt)
            for enemy in killed:
                self.gold += enemy.gold_reward
                self.renderer.add_damage_number(
                    int(enemy.x), int(enemy.y) - 20,
                    f"+{enemy.gold_reward}g", (255, 215, 0)
                )
                self.renderer.add_particles(
                    int(enemy.x), int(enemy.y), 8, (200, 60, 60)
                )
            if hasattr(tower, 'target') and tower.target is not None:
                if tower.attack_cooldown >= tower.attack_speed - 0.05:
                    self._spawn_projectile(tower)
                    if isinstance(tower, ArtilleryTower):
                        splash_size = int(
                            tower.splash_radius * tower.tile_size)
                        self.renderer.spawn_effect(
                            int(tower.target.x), int(tower.target.y),
                            "explosion", max(48, splash_size)
                        )

        for tower in self.towers:
            if isinstance(tower, NecromancerTower):
                heal = tower.get_pending_heal()
                if heal > 0:
                    self.base_hp = min(self.base_max_hp,
                                       self.base_hp + heal)

        self._update_projectiles(dt)
        prev_count = len(self.enemies)
        self.enemies = [e for e in self.enemies if e.is_alive]
        new_count = len(self.enemies)

        if self.wave_manager.is_round_clear(self.enemies):
            self._on_round_clear()

    # ------------------------------------------------------------------
    # Combat helpers
    # ------------------------------------------------------------------

    def _get_enemy_base_damage(self, enemy):
        """Determine how much base HP an enemy removes on reaching the end.

        Args:
            enemy: Enemy instance.

        Returns:
            Integer damage to the base.
        """
        damage_map = {
            EnemyType.GRUNT: 1,
            EnemyType.RUNNER: 1,
            EnemyType.ARMORED: 2,
            EnemyType.BOMBER: 2,
            EnemyType.BOSS: 5,
        }
        raw = damage_map.get(enemy.enemy_type, 1)
        return max(1, raw - self.base_armor)

    def _process_bomber_attacks(self, dt):
        """Let bomber enemies throw bombs at nearby towers."""
        bomb_range = self.game_map.tile_size * 2.5
        for enemy in self.enemies:
            if not enemy.is_alive or enemy.tower_damage <= 0:
                continue
            enemy.bomb_cooldown -= dt
            if enemy.bomb_cooldown > 0:
                continue

            nearest_tower = None
            nearest_dist = bomb_range
            for tower in self.towers:
                if tower.is_destroyed:
                    continue
                dx = tower.pixel_x - enemy.x
                dy = tower.pixel_y - enemy.y
                dist = math.sqrt(dx * dx + dy * dy)
                if dist < nearest_dist:
                    nearest_dist = dist
                    nearest_tower = tower

            if nearest_tower is not None:
                nearest_tower.take_tower_damage(enemy.tower_damage)
                enemy.bomb_cooldown = enemy.bomb_interval
                self.renderer.add_particles(
                    nearest_tower.pixel_x, nearest_tower.pixel_y,
                    5, (255, 140, 40)
                )

    def _remove_destroyed_towers(self):
        """Remove any towers that have been destroyed by bombers."""
        destroyed = [t for t in self.towers if t.is_destroyed]
        for tower in destroyed:
            self.game_map.add_build_spot(tower.x, tower.y)
            if tower is self.selected_tower:
                self.selected_tower = None
            self.renderer.add_particles(
                tower.pixel_x, tower.pixel_y, 12, (180, 80, 30)
            )
        self.towers = [t for t in self.towers if not t.is_destroyed]

    def _on_round_clear(self):
        """Handle a completed round — enter prep phase with countdown."""
        bonus = self.config["gameplay"]["round_bonus_gold"]
        self.gold += bonus
        self.highest_round = max(self.highest_round, self.current_round)
        self.wave_countdown = self.wave_countdown_max
        self.prep_phase = True
        self.moving_tower = None

    # ------------------------------------------------------------------
    # Rendering delegation
    # ------------------------------------------------------------------

    def render(self):
        """Render the current frame based on game state."""
        if self.state == GameState.MENU:
            self.renderer.draw_menu()
        elif self.state == GameState.PLAYING:
            self._render_gameplay()
        elif self.state == GameState.PAUSED:
            self._render_gameplay()
            self.renderer.draw_pause_overlay(
                music_muted=self.music_muted,
                music_volume=self.music_volume,
                debug_mode=self.debug_mode
            )
        elif self.state == GameState.ROUND_FAILED:
            self._render_gameplay()
            self.renderer.draw_round_failed(self.current_round)

    def _render_gameplay(self):
        """Render the active gameplay scene."""
        mouse_pos = pygame.mouse.get_pos()
        hover_col, hover_row = self.game_map.get_grid_pos(
            mouse_pos[0], mouse_pos[1]
        )
        all_soldiers = self._get_all_soldiers()
        unlocked = {t: self._is_tower_unlocked(t)
                    for t in self.config["tower_unlocks"]}

        self.renderer.draw_game(
            game_map=self.game_map,
            towers=self.towers,
            enemies=self.enemies,
            soldiers=all_soldiers,
            projectiles=self.projectiles,
            gold=self.gold,
            base_hp=self.base_hp,
            base_max_hp=self.base_max_hp,
            round_number=self.current_round,
            selected_tower_type=self.selected_tower_type,
            hover_pos=(hover_col, hover_row),
            selected_tower=self.selected_tower,
            tower_unlocks=unlocked,
            round_timer=self.round_timer,
            game_speed=self.game_speed,
            base_level=self.base_level,
            selected_base=self.selected_base,
            show_skip=False,
            base_armor=self.base_armor,
            base_wp=self.base_wp,
            selected_build_spot=self.selected_build_spot,
            debug_mode=self.debug_mode,
            prep_phase=self.prep_phase,
            prep_countdown=self.wave_countdown,
            prep_countdown_max=self.wave_countdown_max,
            moving_tower=self.moving_tower,
        )

    # ------------------------------------------------------------------
    # Projectile management
    # ------------------------------------------------------------------

    def _spawn_projectile(self, tower):
        """Create a visual projectile from tower to target.

        Args:
            tower: Tower that fired.
        """
        skip_types = (TowerType.BARRACKS, TowerType.TESLA, TowerType.LASER)
        if tower.tower_type in skip_types:
            return
        proj = {
            "x": float(tower.pixel_x),
            "y": float(tower.pixel_y),
            "target_x": tower.target.x,
            "target_y": tower.target.y,
            "speed": 6.0,
            "tower_type": tower.tower_type,
            "timer": 0.5
        }
        self.projectiles.append(proj)

    def _update_projectiles(self, dt):
        """Move projectiles toward targets and remove expired ones.

        Args:
            dt: Delta time in seconds.
        """
        alive = []
        for proj in self.projectiles:
            proj["timer"] -= dt
            dx = proj["target_x"] - proj["x"]
            dy = proj["target_y"] - proj["y"]
            dist = math.sqrt(dx * dx + dy * dy)
            if dist < proj["speed"] or proj["timer"] <= 0:
                continue
            proj["x"] += (dx / dist) * proj["speed"]
            proj["y"] += (dy / dist) * proj["speed"]
            alive.append(proj)
        self.projectiles = alive

    # ------------------------------------------------------------------
    # Soldier helpers
    # ------------------------------------------------------------------

    def _get_all_soldiers(self):
        """Collect all living soldiers from barracks towers.

        Returns:
            List of all active Soldier instances.
        """
        all_soldiers = []
        for tower in self.towers:
            if isinstance(tower, BarracksTower):
                all_soldiers.extend(tower.get_all_soldiers())
        return all_soldiers

    # ------------------------------------------------------------------
    # Game lifecycle
    # ------------------------------------------------------------------

    def _start_new_game(self):
        """Start a fresh game from the menu."""
        self.game_map = GameMap(self.config)
        self.wave_manager = WaveManager(self.config)
        self.towers = []
        self.enemies = []
        self.projectiles = []
        self.gold = self.config["gameplay"]["starting_gold"]
        self.base_level = 1
        self.base_max_hp = self.config["gameplay"]["base_upgrade_hp"][0]
        self.base_hp = self.base_max_hp
        self.current_round = 0
        self.highest_round = 0
        self.selected_tower_type = None
        self.selected_tower = None
        self.selected_base = False
        self.selected_build_spot = None
        self.round_timer = 0.0
        self.game_speed = 1
        self.base_armor = self.config["gameplay"]["base_upgrade_armor"][0]
        self.wave_countdown = 0.0
        self.prep_phase = False
        self.moving_tower = None
        waypoints = self.game_map.get_path_pixel_waypoints()
        self.base_wp = waypoints[-1] if waypoints else None
        self._begin_next_round()

    def _begin_next_round(self):
        """Start the next round. Bonus gold for time left on the countdown."""
        early_bonus = max(0, int(self.wave_countdown))
        if early_bonus > 0:
            self.gold += early_bonus
            self.renderer.add_damage_number(
                self.config["screen"]["width"] // 2,
                self.config["screen"]["height"] // 2 - 40,
                f"+{early_bonus}g early!", (100, 255, 100)
            )
        self.wave_countdown = 0.0
        self.prep_phase = False
        self.moving_tower = None
        self.current_round += 1
        self.enemies = []
        self.projectiles = []
        self.round_timer = 0.0
        self._reset_soldiers()
        self.wave_manager.start_round(self.current_round)
        self.state = GameState.PLAYING

    def _retry_round(self):
        """Retry the current round — reset enemies and base HP."""
        self.enemies = []
        self.projectiles = []
        self.base_hp = self.base_max_hp
        self.round_timer = 0.0
        self._reset_soldiers()
        self.wave_manager.start_round(self.current_round)
        self.state = GameState.PLAYING

    def _full_restart(self):
        """Full restart from round 1 — reset everything."""
        self._start_new_game()

    def _reset_soldiers(self):
        """Respawn all soldiers in barracks towers to full HP."""
        for tower in self.towers:
            if isinstance(tower, BarracksTower):
                tower.soldiers = []
                tower._spawn_initial_soldiers()
