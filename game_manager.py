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
from tower import create_tower, BarracksTower, NecromancerTower, ArtilleryTower
from renderer import Renderer


class GameManager:
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
        self.idle_timer = 0.0
        self.debug_mode = False
        self.music_volume = 0.3
        self.music_muted = False
        self.wave_countdown = 0.0
        self.wave_countdown_max = 60.0
        self.gold_drip_accum = 0.0
        waypoints = self.game_map.get_path_pixel_waypoints()
        self.base_wp = waypoints[-1] if waypoints else None

    def handle_event(self, event):
        """Process a single pygame event based on current game state.

        Args:
            event: A pygame event.
        """
        handlers = {
            GameState.MENU: self._handle_menu_event,
            GameState.PLAYING: self._handle_playing_event,
            GameState.PAUSED: self._handle_paused_event,
            GameState.ROUND_COMPLETE: self._handle_round_complete_event,
            GameState.ROUND_FAILED: self._handle_round_failed_event,
            GameState.GAME_OVER: self._handle_game_over_event,
        }
        handler = handlers.get(self.state)
        if handler is not None:
            handler(event)

    def _handle_menu_event(self, event):
        """Handle events in the menu state.

        Args:
            event: A pygame event.
        """
        if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
            self._start_new_game()

    def _handle_playing_event(self, event):
        """Handle events during gameplay.

        Args:
            event: A pygame event.
        """
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                if (self.selected_tower_type is not None
                        or self.selected_tower is not None
                        or self.selected_base
                        or self.selected_build_spot is not None):
                    self.selected_tower_type = None
                    self.selected_tower = None
                    self.selected_base = False
                    self.selected_build_spot = None
                else:
                    self.state = GameState.PAUSED
            elif event.key == pygame.K_F3:
                self.debug_mode = not self.debug_mode
            elif event.key == pygame.K_1:
                self._select_tower_type(TowerType.FORTRESS)
            elif event.key == pygame.K_2:
                self._select_tower_type(TowerType.ARCHER)
            elif event.key == pygame.K_3:
                self._select_tower_type(TowerType.BARRACKS)
            elif event.key == pygame.K_4:
                self._select_tower_type(TowerType.MAGE)
            elif event.key == pygame.K_5:
                self._select_tower_type(TowerType.ARTILLERY)
            elif event.key == pygame.K_6:
                self._select_tower_type(TowerType.FREEZE)
            elif event.key == pygame.K_7:
                self._select_tower_type(TowerType.POISON)
            elif event.key == pygame.K_8:
                self._select_tower_type(TowerType.BALLISTA)
            elif event.key == pygame.K_9:
                self._select_tower_type(TowerType.TESLA)
            elif event.key == pygame.K_0:
                self._select_tower_type(TowerType.NECROMANCER)
            elif self.debug_mode and event.key == pygame.K_g:
                self.gold += 500
            elif self.debug_mode and event.key == pygame.K_k:
                for enemy in self.enemies:
                    enemy.is_alive = False
            elif self.debug_mode and event.key == pygame.K_u:
                self.highest_round = 999
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            self._handle_click(event.pos)

    def _handle_paused_event(self, event):
        """Handle events in the paused state (settings menu).

        Args:
            event: A pygame event.
        """
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE or event.key == pygame.K_p:
                self.state = GameState.PLAYING
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            self._handle_settings_click(event.pos)

    def _handle_settings_click(self, mouse_pos):
        """Handle clicks on the settings/pause menu."""
        rects = self.renderer.get_settings_rects()

        if rects["mute"].collidepoint(mouse_pos):
            self.music_muted = not self.music_muted
            if self.music_muted:
                pygame.mixer.music.set_volume(0)
            else:
                pygame.mixer.music.set_volume(self.music_volume)

        if rects["vol_up"].collidepoint(mouse_pos):
            self.music_volume = min(1.0, self.music_volume + 0.1)
            if not self.music_muted:
                pygame.mixer.music.set_volume(self.music_volume)

        if rects["vol_down"].collidepoint(mouse_pos):
            self.music_volume = max(0.0, self.music_volume - 0.1)
            if not self.music_muted:
                pygame.mixer.music.set_volume(self.music_volume)

        if rects["debug"].collidepoint(mouse_pos):
            self.debug_mode = not self.debug_mode

        if rects["resume"].collidepoint(mouse_pos):
            self.state = GameState.PLAYING

    def _handle_round_complete_event(self, event):
        """Handle events on the round complete screen.

        Args:
            event: A pygame event.
        """
        activated = False
        if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
            activated = True
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            btn = self.renderer.get_next_round_button_rect()
            if btn.collidepoint(event.pos):
                activated = True

        if activated:
            self._begin_next_round()

    def _handle_round_failed_event(self, event):
        """Handle events on the round failed screen.

        Args:
            event: A pygame event.
        """
        activated = False
        if event.type == pygame.KEYDOWN and event.key == pygame.K_r:
            activated = True
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            btn = self.renderer.get_retry_button_rect()
            if btn.collidepoint(event.pos):
                activated = True

        if activated:
            self._retry_round()
            return

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            full_btn = self.renderer.get_full_restart_button_rect()
            if full_btn.collidepoint(event.pos):
                self._full_restart()

    def _handle_game_over_event(self, event):
        """Handle events on the game over screen.

        Args:
            event: A pygame event.
        """
        activated = False
        if event.type == pygame.KEYDOWN and event.key == pygame.K_r:
            activated = True
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            btn = self.renderer.get_restart_button_rect()
            if btn.collidepoint(event.pos):
                activated = True

        if activated:
            self._full_restart()

    def _handle_click(self, mouse_pos):
        """Handle mouse click during gameplay.

        Args:
            mouse_pos: Tuple (x, y) pixel position of click.
        """
        speed_rect = self.renderer.get_speed_button_rect()
        if speed_rect.collidepoint(mouse_pos):
            self._toggle_speed()
            return

        pause_rect = self.renderer.get_pause_button_rect()
        if pause_rect.collidepoint(mouse_pos):
            self.state = GameState.PAUSED
            return

        button_rects = self.renderer.get_tower_button_rects()
        for tower_type, rect in button_rects:
            if rect.collidepoint(mouse_pos):
                self._select_tower_type(tower_type)
                self.selected_tower = None
                self.selected_base = False
                return

        if self.selected_tower is not None:
            upg_rect = self.renderer.get_upgrade_button_rect(self.selected_tower)
            sell_rect = self.renderer.get_sell_button_rect(self.selected_tower)
            if upg_rect.collidepoint(mouse_pos):
                self._try_upgrade_tower()
                return
            if sell_rect.collidepoint(mouse_pos):
                self._try_sell_tower()
                return

        if self.selected_base:
            base_upg = self.renderer.get_base_upgrade_button_rect()
            if base_upg is not None and base_upg.collidepoint(mouse_pos):
                self._try_upgrade_base()
                return

        if self._is_base_click(mouse_pos):
            self.selected_base = True
            self.selected_tower = None
            self.selected_tower_type = None
            return

        self.selected_base = False

        if self.selected_build_spot is not None:
            build_menu_result = self._check_build_menu_click(mouse_pos)
            if build_menu_result is not None:
                bcol, brow = self.selected_build_spot
                self.selected_tower_type = build_menu_result
                self._try_place_tower(bcol, brow)
                self.selected_build_spot = None
                return
            self.selected_build_spot = None

        col, row = self.game_map.get_grid_pos(mouse_pos[0], mouse_pos[1])

        if self.game_map.is_locked_spot(col, row):
            self._try_unlock_slot(col, row)
            return

        if self.selected_tower_type is not None:
            self._try_place_tower(col, row)
        elif self.game_map.is_build_spot(col, row):
            self.selected_build_spot = (col, row)
            self.selected_tower = None
        else:
            self._try_select_placed_tower(col, row)

    def _is_base_click(self, mouse_pos):
        """Check if a click is on or near the base castle."""
        waypoints = self.game_map.get_path_pixel_waypoints()
        if not waypoints:
            return False
        bx, by = waypoints[-1]
        dx = mouse_pos[0] - bx
        dy = mouse_pos[1] - by
        return (dx * dx + dy * dy) <= (self.game_map.tile_size * 0.8) ** 2

    def _is_tower_unlocked(self, tower_type):
        """Check if a tower type is unlocked at the current round.

        Args:
            tower_type: TowerType to check.

        Returns:
            True if the tower is unlocked.
        """
        unlock_round = self.config["tower_unlocks"].get(tower_type, 1)
        return self.highest_round >= unlock_round or self.current_round >= unlock_round

    def _select_tower_type(self, tower_type):
        """Select a tower type for placement (only if unlocked).

        Args:
            tower_type: TowerType to select.
        """
        if not self._is_tower_unlocked(tower_type):
            return
        if self.selected_tower_type == tower_type:
            self.selected_tower_type = None
        else:
            self.selected_tower_type = tower_type
            self.selected_tower = None

    def _try_place_tower(self, col, row):
        """Attempt to place a tower at the given grid position.

        Args:
            col: Grid column.
            row: Grid row.
        """
        if not self.game_map.is_build_spot(col, row):
            return

        cost = self.config["towers"][self.selected_tower_type]["cost"]
        if self.gold < cost:
            return

        tower = create_tower(
            self.selected_tower_type, col, row,
            self.config, self.game_map.tile_size,
            game_map=self.game_map
        )
        self.towers.append(tower)
        self.gold -= cost
        self.game_map.remove_build_spot(col, row)
        self.selected_tower_type = None

    def _try_unlock_slot(self, col, row):
        """Attempt to unlock a locked build spot by spending gold.

        Args:
            col: Grid column.
            row: Grid row.
        """
        if not self.game_map.is_locked_spot(col, row):
            return
        cost = self.config["gameplay"]["slot_unlock_cost"]
        if self.gold < cost:
            return
        if self.game_map.unlock_spot(col, row):
            self.gold -= cost
            self.renderer.invalidate_grass_cache()

    def _try_select_placed_tower(self, col, row):
        """Try to select an existing tower at the given grid position.

        Args:
            col: Grid column.
            row: Grid row.
        """
        self.selected_tower = None
        for tower in self.towers:
            if tower.x == col and tower.y == row:
                self.selected_tower = tower
                break

    def _check_build_menu_click(self, mouse_pos):
        """Check if a click hit a tower option in the build menu popup.

        Args:
            mouse_pos: Tuple (x, y) pixel position of click.

        Returns:
            TowerType if a tower was clicked, else None.
        """
        if self.selected_build_spot is None:
            return None
        rects = self.renderer.get_build_menu_rects(self.selected_build_spot)
        for tower_type, rect in rects:
            if rect.collidepoint(mouse_pos) and self._is_tower_unlocked(tower_type):
                cost = self.config["towers"][tower_type]["cost"]
                if self.gold >= cost:
                    return tower_type
        return None

    def _try_upgrade_tower(self):
        """Attempt to upgrade the currently selected tower."""
        if self.selected_tower is None:
            return
        cost = self.selected_tower.get_upgrade_cost()
        if cost == 0 or self.gold < cost:
            return
        if self.selected_tower.upgrade():
            self.gold -= cost

    def _try_sell_tower(self):
        """Sell the currently selected tower."""
        if self.selected_tower is None:
            return
        refund = self.selected_tower.get_sell_value()
        self.gold += refund
        self.game_map.add_build_spot(
            self.selected_tower.x, self.selected_tower.y
        )
        self.towers.remove(self.selected_tower)
        self.selected_tower = None

    def _try_upgrade_base(self):
        """Upgrade the base to increase max HP."""
        max_lvl = len(self.config["gameplay"]["base_upgrade_cost"])
        if self.base_level >= max_lvl:
            return
        cost = self.config["gameplay"]["base_upgrade_cost"][self.base_level]
        if self.gold < cost:
            return
        self.gold -= cost
        self.base_level += 1
        new_max = self.config["gameplay"]["base_upgrade_hp"][self.base_level - 1]
        hp_gain = new_max - self.base_max_hp
        self.base_max_hp = new_max
        self.base_hp = min(self.base_max_hp, self.base_hp + hp_gain)
        self.base_armor = self.config["gameplay"]["base_upgrade_armor"][
            self.base_level - 1
        ]

    def _toggle_speed(self):
        """Cycle game speed: 1x -> 2x -> 3x -> 1x."""
        if self.game_speed == 1:
            self.game_speed = 2
        elif self.game_speed == 2:
            self.game_speed = 3
        else:
            self.game_speed = 1

    def update(self, dt):
        """Update all game entities for one frame.

        Args:
            dt: Delta time in seconds since last frame.
        """
        if self.state == GameState.ROUND_COMPLETE:
            self.wave_countdown -= dt
            if self.wave_countdown <= 0:
                self._begin_next_round()
            return

        if self.state != GameState.PLAYING:
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
                        splash_size = int(tower.splash_radius * tower.tile_size)
                        self.renderer.spawn_effect(
                            int(tower.target.x), int(tower.target.y),
                            "explosion", max(48, splash_size)
                        )

        for tower in self.towers:
            if isinstance(tower, NecromancerTower):
                heal = tower.get_pending_heal()
                if heal > 0:
                    self.base_hp = min(self.base_max_hp, self.base_hp + heal)

        self._update_projectiles(dt)
        prev_count = len(self.enemies)
        self.enemies = [e for e in self.enemies if e.is_alive]
        new_count = len(self.enemies)

        if new_count < prev_count:
            self.idle_timer = 0.0
        elif not self.wave_manager.wave_active and new_count > 0:
            self.idle_timer += dt
        else:
            self.idle_timer = 0.0

        if self.wave_manager.is_round_clear(self.enemies):
            self._on_round_clear()

    def _get_enemy_base_damage(self, enemy):
        """Determine how much base HP an enemy removes on reaching the end.

        Bosses deal more damage than regular enemies.

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
        """Handle a completed round — start countdown to next wave."""
        bonus = self.config["gameplay"]["round_bonus_gold"]
        self.gold += bonus
        self.highest_round = max(self.highest_round, self.current_round)
        self.wave_countdown = self.wave_countdown_max
        self.gold_drip_accum = 0.0
        self.state = GameState.ROUND_COMPLETE

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
        elif self.state == GameState.ROUND_COMPLETE:
            self._render_gameplay()
            self.renderer.draw_round_complete(
                self.current_round,
                self.config["gameplay"]["round_bonus_gold"],
                int(self.wave_countdown)
            )
        elif self.state == GameState.ROUND_FAILED:
            self._render_gameplay()
            self.renderer.draw_round_failed(self.current_round)
        elif self.state == GameState.GAME_OVER:
            self.renderer.draw_game_over(self.highest_round)

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
            debug_mode=self.debug_mode
        )

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
        self.idle_timer = 0.0
        self.wave_countdown = 0.0
        self.gold_drip_accum = 0.0
        waypoints = self.game_map.get_path_pixel_waypoints()
        self.base_wp = waypoints[-1] if waypoints else None
        self._begin_next_round()

    def _begin_next_round(self):
        """Start the next round. Bonus gold for time left on the countdown."""
        early_bonus = max(0, int(self.wave_countdown))
        if early_bonus > 0:
            self.gold += early_bonus
        self.wave_countdown = 0.0
        self.current_round += 1
        self.enemies = []
        self.projectiles = []
        self.round_timer = 0.0
        self._reset_soldiers()
        self.wave_manager.start_round(self.current_round)
        self.state = GameState.PLAYING

    def _retry_round(self):
        """Retry the current round — same round number, reset enemies and base HP."""
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
