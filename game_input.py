"""Game input handler mixin.

Processes all pygame events and click actions for the game manager.
Split from ``game_manager.py`` for readability — methods reference
``self`` attributes owned by ``GameManager``.
"""

import pygame
from enums import GameState, TowerType


class GameInputMixin:
    """Mixin providing event and click handling for GameManager."""

    def handle_event(self, event):
        """Process a single pygame event based on current game state.

        Args:
            event: A pygame event.
        """
        handlers = {
            GameState.MENU: self._handle_menu_event,
            GameState.PLAYING: self._handle_playing_event,
            GameState.PAUSED: self._handle_paused_event,
            GameState.ROUND_FAILED: self._handle_round_failed_event,
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
        """Handle events during gameplay (including prep phase).

        Args:
            event: A pygame event.
        """
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE and self.prep_phase:
                self._begin_next_round()
                return
            if event.key == pygame.K_ESCAPE:
                if self.moving_tower is not None:
                    self.moving_tower = None
                elif (self.selected_tower_type is not None
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

    def _handle_round_failed_event(self, event):
        """Handle events on the round failed screen.

        Args:
            event: A pygame event.
        """
        if event.type == pygame.KEYDOWN and event.key == pygame.K_r:
            self._full_restart()
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            btn = self.renderer.get_full_restart_button_rect()
            if btn.collidepoint(event.pos):
                self._full_restart()

    def _handle_click(self, mouse_pos):
        """Handle mouse click during gameplay.

        Args:
            mouse_pos: Tuple (x, y) pixel position of click.
        """
        if self._handle_click_prep_phase(mouse_pos):
            return
        if self._handle_click_hud_buttons(mouse_pos):
            return
        if self._handle_click_radial_menus(mouse_pos):
            return
        self._handle_click_grid(mouse_pos)

    def _handle_click_prep_phase(self, mouse_pos):
        """Handle prep-phase-specific clicks (next wave, tower move)."""
        if self.prep_phase:
            nw_rect = self.renderer.get_next_wave_button_rect()
            if nw_rect.collidepoint(mouse_pos):
                self._begin_next_round()
                return True
        if self.prep_phase and self.moving_tower is not None:
            col, row = self.game_map.get_grid_pos(
                mouse_pos[0], mouse_pos[1])
            if self.game_map.is_build_spot(col, row):
                self._move_tower_to(col, row)
                return True
            self.moving_tower = None
        return False

    def _handle_click_hud_buttons(self, mouse_pos):
        """Handle speed, pause, and tower-bar button clicks."""
        speed_rect = self.renderer.get_speed_button_rect()
        if speed_rect.collidepoint(mouse_pos):
            self._toggle_speed()
            return True

        pause_rect = self.renderer.get_pause_button_rect()
        if pause_rect.collidepoint(mouse_pos):
            self.state = GameState.PAUSED
            return True

        button_rects = self.renderer.get_tower_button_rects()
        for tower_type, rect in button_rects:
            if rect.collidepoint(mouse_pos):
                self._select_tower_type(tower_type)
                self.selected_tower = None
                self.selected_base = False
                return True
        return False

    def _handle_click_radial_menus(self, mouse_pos):
        """Handle clicks on tower upgrade/sell and base upgrade radials."""
        if self.selected_tower is not None:
            upg_rect = self.renderer.get_upgrade_button_rect(
                self.selected_tower)
            sell_rect = self.renderer.get_sell_button_rect(
                self.selected_tower)
            if upg_rect.collidepoint(mouse_pos):
                self._try_upgrade_tower()
                return True
            if sell_rect.collidepoint(mouse_pos):
                self._try_sell_tower()
                return True

        if self.selected_base:
            base_upg = self.renderer.get_base_upgrade_button_rect()
            if base_upg is not None and base_upg.collidepoint(mouse_pos):
                self._try_upgrade_base()
                return True

        if self._is_base_click(mouse_pos):
            self.selected_base = True
            self.selected_tower = None
            self.selected_tower_type = None
            return True
        return False

    def _handle_click_grid(self, mouse_pos):
        """Handle clicks on the map grid (build, select, unlock)."""
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
        return (self.highest_round >= unlock_round
                or self.current_round >= unlock_round)

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

        from tower import create_tower
        tower = create_tower(
            self.selected_tower_type, col, row,
            self.config, self.game_map.tile_size,
            game_map=self.game_map
        )
        self.towers.append(tower)
        self.gold -= cost
        self.game_map.remove_build_spot(col, row)
        self.selected_tower_type = None
        self.renderer.invalidate_grass_cache()

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

        During prep phase, the first click selects for movement; a second
        click on an empty build spot completes the move.

        Args:
            col: Grid column.
            row: Grid row.
        """
        self.selected_tower = None
        for tower in self.towers:
            if tower.x == col and tower.y == row:
                self.selected_tower = tower
                if self.prep_phase:
                    self.moving_tower = tower
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
            if (rect.collidepoint(mouse_pos)
                    and self._is_tower_unlocked(tower_type)):
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
        self.renderer.invalidate_grass_cache()

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
        new_max = self.config["gameplay"]["base_upgrade_hp"][
            self.base_level - 1]
        hp_gain = new_max - self.base_max_hp
        self.base_max_hp = new_max
        self.base_hp = min(self.base_max_hp, self.base_hp + hp_gain)
        self.base_armor = self.config["gameplay"]["base_upgrade_armor"][
            self.base_level - 1
        ]

    def _move_tower_to(self, col, row):
        """Move the selected tower to a new build spot (prep phase only).

        Args:
            col: Target grid column.
            row: Target grid row.
        """
        tower = self.moving_tower
        if tower is None:
            return
        old_col, old_row = tower.x, tower.y
        self.game_map.add_build_spot(old_col, old_row)
        tower.x = col
        tower.y = row
        ts = self.game_map.tile_size
        tower.pixel_x = col * ts + ts // 2
        tower.pixel_y = row * ts + ts // 2
        self.game_map.remove_build_spot(col, row)
        self.moving_tower = None
        self.selected_tower = tower
        self.renderer.invalidate_grass_cache()

    def _toggle_speed(self):
        """Cycle game speed: 1x -> 2x -> 3x -> 1x."""
        if self.game_speed == 1:
            self.game_speed = 2
        elif self.game_speed == 2:
            self.game_speed = 3
        else:
            self.game_speed = 1
