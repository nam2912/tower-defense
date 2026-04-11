"""Mixin for HUD elements: tower bar, radial menus, info boxes, debug."""

import math
import pygame
from enums import TowerType


class RendererHudMixin:

    def _draw_ui_panel(self, gold, base_hp, base_max_hp, round_number,
                       selected_tower_type, selected_tower,
                       tower_unlocks=None, round_timer=0.0, game_speed=1,
                       base_level=1, selected_base=False, show_skip=False,
                       base_armor=0):
        """Draw the floating HUD elements overlaid on the game map."""
        self._draw_hud_top_left(base_hp, base_max_hp, gold, round_number,
                                base_armor)
        self._draw_hud_top_right(game_speed, round_timer, show_skip)
        self._draw_tower_bar(selected_tower_type, gold, tower_unlocks)

        if selected_tower is not None:
            self._draw_radial_menu(selected_tower, gold)
        if selected_base:
            self._draw_base_radial(base_level, gold)
        if selected_tower_type is not None:
            self._draw_placement_tooltip(selected_tower_type)

    def _draw_hud_badge(self, x, y, w, h):
        """Draw a HUD badge using a tinted panel sprite."""
        tinted = self._tinted_panel(w, h, (35, 28, 18))
        if tinted is not None:
            self.screen.blit(tinted, (x, y))
        else:
            pygame.draw.rect(self.screen, (35, 28, 18),
                             (x, y, w, h), border_radius=8)
        pygame.draw.rect(self.screen, (160, 130, 70),
                         (x, y, w, h), 2, border_radius=8)

    def _draw_hud_top_left(self, base_hp, base_max_hp, gold, round_number,
                           base_armor=0):
        """Draw the top-left HUD: HP bar, armor, gold, wave counter."""
        badge_h = 92 if base_armor > 0 else 82
        self._draw_hud_badge(6, 6, 172, badge_h)

        pygame.draw.circle(self.screen, (220, 40, 40), (24, 20), 8)
        pygame.draw.circle(self.screen, (180, 20, 20), (24, 20), 8, 2)
        hp_text = self.font_medium.render(f"{base_hp}/{base_max_hp}", True,
                                          (255, 255, 255))
        self.screen.blit(hp_text, (36, 10))

        bar_x, bar_y, bar_w, bar_h = 16, 34, 150, 10
        ratio = base_hp / base_max_hp if base_max_hp > 0 else 0
        pygame.draw.rect(self.screen, (50, 15, 15),
                         (bar_x, bar_y, bar_w, bar_h), border_radius=4)
        fg_w = int(bar_w * ratio)
        if ratio > 0.6:
            bar_c = (40, 200, 50)
        elif ratio > 0.3:
            bar_c = (220, 180, 30)
        else:
            bar_c = (220, 40, 30)
        if fg_w > 0:
            pygame.draw.rect(self.screen, bar_c,
                             (bar_x, bar_y, fg_w, bar_h), border_radius=4)
        pygame.draw.rect(self.screen, (180, 180, 180),
                         (bar_x, bar_y, bar_w, bar_h), 1, border_radius=4)

        info_y = 48
        if base_armor > 0:
            shield_cx, shield_cy = 24, info_y + 2
            pts = [(shield_cx, shield_cy - 7), (shield_cx - 6, shield_cy - 3),
                   (shield_cx - 6, shield_cy + 3), (shield_cx, shield_cy + 7),
                   (shield_cx + 6, shield_cy + 3), (shield_cx + 6, shield_cy - 3)]
            pygame.draw.polygon(self.screen, (100, 140, 200), pts)
            pygame.draw.polygon(self.screen, (60, 100, 160), pts, 1)
            armor_txt = self.font_tiny.render(f"Armor {base_armor}", True,
                                              (160, 200, 255))
            self.screen.blit(armor_txt, (36, info_y - 3))
            info_y += 16

        pygame.draw.circle(self.screen, (255, 200, 0), (24, info_y + 8), 8)
        pygame.draw.circle(self.screen, (200, 150, 0), (24, info_y + 8), 8, 2)
        g_sym = self.font_tiny.render("$", True, (140, 100, 0))
        self.screen.blit(g_sym, g_sym.get_rect(center=(24, info_y + 8)))
        gold_text = self.font_medium.render(str(gold), True, (255, 220, 80))
        self.screen.blit(gold_text, (36, info_y))

        badge_bottom = 6 + badge_h + 4
        self._draw_hud_badge(6, badge_bottom, 100, 24)
        wave_text = self.font_small.render(f"Round {round_number}", True,
                                           (255, 200, 100))
        self.screen.blit(wave_text, (14, badge_bottom + 3))

    def _draw_hud_top_right(self, game_speed, round_timer, show_skip=False):
        """Draw the top-right HUD: pause, speed, timer, and skip button."""
        screen_w = self.config["screen"]["width"]
        mouse = pygame.mouse.get_pos()

        pause_r = self.get_pause_button_rect()
        ph = pause_r.collidepoint(mouse)
        self._blit_ui_btn("btn_square_grey", pause_r, ph,
                          tint=(60, 60, 80))
        cx, cy = pause_r.centerx, pause_r.centery
        pygame.draw.rect(self.screen, (220, 220, 240),
                         (cx - 5, cy - 7, 4, 14))
        pygame.draw.rect(self.screen, (220, 220, 240),
                         (cx + 1, cy - 7, 4, 14))

        speed_r = self.get_speed_button_rect()
        sh = speed_r.collidepoint(mouse)
        speed_colors = {1: (140, 140, 160), 2: (220, 200, 60),
                        3: (255, 100, 60)}
        sc = speed_colors.get(game_speed, (140, 140, 160))
        speed_keys = {1: "btn_square_grey", 2: "btn_square_green",
                      3: "btn_square_green"}
        spd_key = speed_keys.get(game_speed, "btn_square_grey")
        spd_tint = (60, 60, 80) if game_speed == 1 else (50, 100, 50)
        self._blit_ui_btn(spd_key, speed_r, sh, tint=spd_tint)
        label = self.font_small.render(f"x{game_speed}", True, sc)
        self.screen.blit(label, label.get_rect(center=speed_r.center))

        minutes = int(round_timer) // 60
        seconds = int(round_timer) % 60
        time_str = f"{minutes:02d}:{seconds:02d}"
        timer_text = self.font_tiny.render(time_str, True, (220, 220, 240))
        tw = timer_text.get_width()
        badge_w = tw + 26
        timer_bg = pygame.Rect(screen_w - badge_w - 6, 40, badge_w, 20)
        tinted_timer = self._tinted_panel(badge_w, 20, (30, 30, 45))
        if tinted_timer is not None:
            self.screen.blit(tinted_timer, timer_bg.topleft)
        else:
            pygame.draw.rect(self.screen, (30, 30, 45), timer_bg,
                             border_radius=4)
        pygame.draw.rect(self.screen, (100, 100, 130), timer_bg, 1,
                         border_radius=4)
        clock_cx = timer_bg.x + 10
        clock_cy = timer_bg.centery
        pygame.draw.circle(self.screen, (180, 180, 210),
                           (clock_cx, clock_cy), 6, 1)
        pygame.draw.line(self.screen, (220, 220, 240),
                         (clock_cx, clock_cy), (clock_cx, clock_cy - 4), 1)
        pygame.draw.line(self.screen, (220, 220, 240),
                         (clock_cx, clock_cy), (clock_cx + 3, clock_cy), 1)
        self.screen.blit(timer_text,
                         (clock_cx + 10, timer_bg.centery
                          - timer_text.get_height() // 2))

        if show_skip:
            skip_r = self.get_skip_button_rect()
            if skip_r is not None:
                skh = skip_r.collidepoint(mouse)
                self._blit_ui_btn("btn_red", skip_r, skh,
                                  tint=(180, 80, 40))
                sk_label = self.font_small.render("SKIP >>", True,
                                                   (255, 230, 180))
                self.screen.blit(sk_label,
                                 sk_label.get_rect(center=skip_r.center))

    # ------------------------------------------------------------------
    # Radial menus
    # ------------------------------------------------------------------

    def _draw_radial_menu(self, tower, gold):
        """Draw Kingdom Rush-style radial upgrade/sell buttons around a tower."""
        cx, cy = tower.pixel_x, tower.pixel_y
        ring_r = self.tile_size // 2 + 20
        pygame.draw.circle(self.screen, (80, 80, 80),
                           (cx, cy), ring_r, 3)

        upg_rect = self.get_upgrade_button_rect(tower)
        sell_rect = self.get_sell_button_rect(tower)
        mouse = pygame.mouse.get_pos()

        upgrade_cost = tower.get_upgrade_cost()
        if upgrade_cost > 0:
            self._draw_radial_btn(upg_rect, mouse, gold >= upgrade_cost,
                                  is_upgrade=True, cost=upgrade_cost)

        slh = sell_rect.collidepoint(mouse)
        self._blit_ui_btn("btn_square_grey", sell_rect, slh,
                          tint=(80, 70, 30))

        sell_icon = self.assets.ui.get("icon_sell")
        if sell_icon is not None:
            iw, ih = sell_icon.get_size()
            self.screen.blit(sell_icon,
                             (sell_rect.centerx - iw // 2,
                              sell_rect.centery - ih // 2 - 4))
        sell_val = self.font_tiny.render(str(tower.get_sell_value()), True,
                                         (200, 200, 160))
        self.screen.blit(sell_val,
                         sell_val.get_rect(center=(sell_rect.centerx,
                                                   sell_rect.centery + 12)))

        info_y = cy + ring_r + 30
        name = tower.tower_type.name.capitalize()
        lines = [
            f"{name} Lv{tower.level}",
            f"DMG:{tower.damage}  RNG:{tower.attack_range:.1f}",
            f"HP:{tower.tower_hp}/{tower.tower_max_hp}  ARM:{tower.tower_armor}",
        ]
        self._draw_info_box(cx, info_y, lines)

    def _draw_radial_btn(self, rect, mouse, can_afford, is_upgrade=True,
                         cost=0):
        """Draw a radial upgrade or sell button using sprite assets.

        Args:
            rect: Button rectangle.
            mouse: Current mouse position.
            can_afford: Whether the player has enough gold.
            is_upgrade: True for upgrade, False for sell.
            cost: Gold cost to display.
        """
        uh = rect.collidepoint(mouse)
        btn_key = "btn_square_green" if can_afford else "btn_square_grey"
        tint_c = (40, 100, 40) if can_afford else (40, 40, 45)
        self._blit_ui_btn(btn_key, rect, uh and can_afford,
                          tint=tint_c)

        icon = self.assets.ui.get(
            "icon_upgrade" if is_upgrade else "icon_sell")
        if icon is not None:
            iw, ih = icon.get_size()
            self.screen.blit(icon, (rect.centerx - iw // 2,
                                     rect.centery - ih // 2 - 4))

        cost_c = (255, 215, 0) if can_afford else (100, 80, 40)
        cost_txt = self.font_tiny.render(str(cost), True, cost_c)
        self.screen.blit(cost_txt,
                         cost_txt.get_rect(center=(rect.centerx,
                                                   rect.centery + 12)))

    def _draw_info_box(self, cx, y, lines):
        """Draw a small info tooltip with multiple text lines.

        Args:
            cx: Center X position.
            y: Top Y position.
            lines: List of text strings to render.
        """
        line_h = 14
        total_h = line_h * len(lines) + 6
        max_w = 0
        rendered = []
        for line in lines:
            txt = self.font_tiny.render(line, True, (255, 255, 220))
            rendered.append(txt)
            max_w = max(max_w, txt.get_width())

        box_w = max_w + 12
        bg_x = cx - box_w // 2
        tinted = self._tinted_panel(box_w, total_h, (20, 16, 10))
        if tinted is not None:
            self.screen.blit(tinted, (bg_x, y - 2))
        else:
            pygame.draw.rect(self.screen, (20, 16, 10),
                             (bg_x, y - 2, box_w, total_h),
                             border_radius=3)
        pygame.draw.rect(self.screen, (100, 100, 120),
                         (bg_x, y - 2, box_w, total_h), 1,
                         border_radius=3)
        for i, txt in enumerate(rendered):
            self.screen.blit(txt,
                             txt.get_rect(center=(cx, y + 5 + i * line_h)))

    def _draw_base_radial(self, base_level, gold):
        """Draw radial upgrade button around the base castle."""
        if self._base_wp is None:
            return
        bx, by = self._base_wp
        ring_r = self.tile_size // 2 + 20
        pygame.draw.circle(self.screen, (200, 160, 50),
                           (bx, by), ring_r, 3)

        upg_rect = self.get_base_upgrade_button_rect()
        if upg_rect is None:
            return
        mouse = pygame.mouse.get_pos()
        max_lvl = len(self.config["gameplay"]["base_upgrade_cost"])
        if base_level < max_lvl:
            cost = self.config["gameplay"]["base_upgrade_cost"][base_level]
            self._draw_radial_btn(upg_rect, mouse, gold >= cost,
                                  is_upgrade=True, cost=cost)
        else:
            self._blit_ui_btn("btn_square_grey", upg_rect, False,
                              tint=(40, 40, 45))
            mx = self.font_tiny.render("MAX", True, (100, 200, 100))
            self.screen.blit(mx, mx.get_rect(center=upg_rect.center))

    def _draw_placement_tooltip(self, tower_type):
        """Draw a small tooltip near the mouse when placing a tower."""
        cfg = self.config["towers"][tower_type]
        name = tower_type.name.capitalize()
        cost = cfg["cost"]
        desc = cfg.get("description", "")
        mouse = pygame.mouse.get_pos()
        tx = mouse[0] + 16
        ty = mouse[1] - 30
        line1 = self.font_small.render(f"{name} ({cost}g)", True,
                                       (255, 255, 220))
        line2 = self.font_tiny.render(desc, True, (180, 200, 160))
        w = max(line1.get_width(), line2.get_width()) + 12
        h = line1.get_height() + line2.get_height() + 8
        screen_w = self.config["screen"]["width"]
        if tx + w > screen_w:
            tx = mouse[0] - w - 8
        tinted = self._tinted_panel(w, h, (20, 18, 12))
        if tinted is not None:
            self.screen.blit(tinted, (tx, ty))
        else:
            pygame.draw.rect(self.screen, (20, 18, 12),
                             (tx, ty, w, h), border_radius=4)
        pygame.draw.rect(self.screen, (100, 90, 60),
                         (tx, ty, w, h), 1, border_radius=4)
        self.screen.blit(line1, (tx + 6, ty + 3))
        self.screen.blit(line2, (tx + 6, ty + 3 + line1.get_height()))

    # ------------------------------------------------------------------
    # Tower bar (bottom-center icons using sprites)
    # ------------------------------------------------------------------

    def _draw_tower_bar(self, selected_tower_type, gold, tower_unlocks=None):
        """Draw tower purchase icons at the bottom-center using sprite icons."""
        tower_types = list(self.assets.towers.keys())
        screen_w = self.config["screen"]["width"]
        screen_h = self.config["screen"]["height"]
        btn_size = 48
        gap = 5
        total_w = len(tower_types) * btn_size + (len(tower_types) - 1) * gap
        start_x = (screen_w - total_w) // 2
        bar_y = screen_h - btn_size - 12

        bar_w = total_w + 20
        bar_h = btn_size + 14
        bx = start_x - 10
        by = bar_y - 7
        bar_rect = (bx, by, bar_w, bar_h)
        tinted = self._tinted_panel(bar_w, bar_h, (35, 30, 20))
        if tinted is not None:
            self.screen.blit(tinted, (bx, by))
        else:
            pygame.draw.rect(self.screen, (35, 30, 20), bar_rect,
                             border_radius=8)
        pygame.draw.rect(self.screen, (140, 115, 65), bar_rect,
                         2, border_radius=8)

        mouse = pygame.mouse.get_pos()

        for i, t_type in enumerate(tower_types):
            x = start_x + i * (btn_size + gap)
            y = bar_y
            rect = pygame.Rect(x, y, btn_size, btn_size)
            unlocked = True
            if tower_unlocks is not None:
                unlocked = tower_unlocks.get(t_type, True)
            cost = self.config["towers"][t_type]["cost"]
            can_afford = gold >= cost and unlocked
            hovering = rect.collidepoint(mouse)

            if not unlocked:
                btn_k = "btn_square_grey"
                tint_c = (35, 30, 25)
            elif selected_tower_type == t_type:
                btn_k = "btn_square_green"
                tint_c = (60, 120, 190)
            elif can_afford:
                btn_k = "btn_square_grey"
                tint_c = (50, 44, 35)
            else:
                btn_k = "btn_square_grey"
                tint_c = (38, 33, 28)

            self._blit_ui_btn(btn_k, rect, hovering and can_afford,
                              tint=tint_c)

            if not unlocked:
                lock_r = self.config["tower_unlocks"].get(t_type, "?")
                lt = self.font_tiny.render(f"R{lock_r}", True, (160, 120, 80))
                self.screen.blit(lt, lt.get_rect(center=(x + btn_size // 2,
                                                          y + btn_size // 2 - 4)))
            else:
                icon = self.assets.get_tower_icon(t_type, (28, 28))
                icx = x + (btn_size - 28) // 2
                icy = y + (btn_size - 28) // 2 - 4
                self.screen.blit(icon, (icx, icy))

            cost_c = (255, 215, 50) if can_afford else (120, 100, 55)
            if not unlocked:
                cost_c = (100, 80, 55)
            ct = self.font_tiny.render(f"{cost}", True, cost_c)
            self.screen.blit(ct,
                             ct.get_rect(center=(x + btn_size // 2,
                                                 y + btn_size - 5)))

    def _draw_tower_info(self, tower, colors, panel_top):
        """No-op: tower info is now shown via radial menu."""

    def _draw_tower_type_tooltip(self, tower_type, panel_top):
        """No-op: tooltip is now drawn via _draw_placement_tooltip."""

    # ------------------------------------------------------------------
    # Build menu
    # ------------------------------------------------------------------

    def _get_build_menu_tower_types(self):
        """Return the ordered list of tower types for the build menu."""
        return [
            TowerType.FORTRESS, TowerType.ARCHER, TowerType.BARRACKS,
            TowerType.MAGE, TowerType.ARTILLERY, TowerType.FREEZE,
            TowerType.POISON, TowerType.BALLISTA, TowerType.TESLA,
            TowerType.NECROMANCER, TowerType.LASER,
        ]

    def get_build_menu_rects(self, build_spot):
        """Get clickable rectangles for each tower option in the build menu.

        Args:
            build_spot: (col, row) of the selected build spot.

        Returns:
            List of (TowerType, pygame.Rect) tuples.
        """
        if build_spot is None:
            return []
        col, row = build_spot
        ts = self.tile_size
        cx = col * ts + ts // 2
        cy = row * ts + ts // 2
        tower_types = self._get_build_menu_tower_types()

        btn_w, btn_h = 44, 52
        gap = 3
        cols_per_row = 4
        total_rows = (len(tower_types) + cols_per_row - 1) // cols_per_row
        panel_w = cols_per_row * btn_w + (cols_per_row - 1) * gap + 16
        panel_h = total_rows * btn_h + (total_rows - 1) * gap + 16

        px = cx - panel_w // 2
        py = cy - panel_h - 20
        sw = self.config["screen"]["width"]
        sh = self.config["screen"]["height"]
        px = max(4, min(px, sw - panel_w - 4))
        py = max(4, min(py, sh - panel_h - 4))

        rects = []
        for i, t_type in enumerate(tower_types):
            r = i // cols_per_row
            c = i % cols_per_row
            bx = px + 8 + c * (btn_w + gap)
            by = py + 8 + r * (btn_h + gap)
            rects.append((t_type, pygame.Rect(bx, by, btn_w, btn_h)))
        return rects

    def _draw_build_menu(self, build_spot, gold, tower_unlocks=None):
        """Draw the tower selection popup above a build spot.

        Args:
            build_spot: (col, row) of the selected build spot.
            gold: Current player gold.
            tower_unlocks: Dict of TowerType -> bool for unlock state.
        """
        rects = self.get_build_menu_rects(build_spot)
        if not rects:
            return

        first_rect = rects[0][1]
        last_rect = rects[-1][1]
        panel_rect = pygame.Rect(first_rect.x - 8, first_rect.y - 8,
                                 last_rect.right - first_rect.x + 16,
                                 last_rect.bottom - first_rect.y + 16)
        tinted = self._tinted_panel(panel_rect.width, panel_rect.height,
                                    (40, 35, 25))
        if tinted is not None:
            self.screen.blit(tinted, panel_rect.topleft)
        else:
            pygame.draw.rect(self.screen, (40, 35, 25), panel_rect,
                             border_radius=8)
        pygame.draw.rect(self.screen, (160, 130, 70), panel_rect,
                         2, border_radius=8)

        mouse = pygame.mouse.get_pos()
        for t_type, rect in rects:
            unlocked = True
            if tower_unlocks is not None:
                unlocked = tower_unlocks.get(t_type, True)
            cost = self.config["towers"][t_type]["cost"]
            can_afford = gold >= cost and unlocked
            hovering = rect.collidepoint(mouse)

            if not unlocked:
                btn_k = "btn_square_grey"
                tint_c = (35, 30, 25)
            elif can_afford:
                btn_k = "btn_square_grey"
                tint_c = (50, 44, 35)
            else:
                btn_k = "btn_square_grey"
                tint_c = (38, 33, 28)

            self._blit_ui_btn(btn_k, rect, hovering and can_afford,
                              tint=tint_c)

            if not unlocked:
                lock_r = self.config["tower_unlocks"].get(t_type, "?")
                lt = self.font_tiny.render(f"R{lock_r}", True, (160, 120, 80))
                self.screen.blit(lt, lt.get_rect(center=(rect.centerx,
                                                          rect.centery - 5)))
            else:
                icon = self.assets.get_tower_icon(t_type, (24, 24))
                self.screen.blit(icon, (rect.centerx - 12,
                                         rect.centery - 17))

            cost_c = (255, 215, 50) if can_afford else (120, 100, 55)
            if not unlocked:
                cost_c = (100, 80, 55)
            ct = self.font_tiny.render(f"{cost}", True, cost_c)
            self.screen.blit(ct,
                             ct.get_rect(center=(rect.centerx,
                                                 rect.bottom - 8)))

    # ------------------------------------------------------------------
    # Debug overlay
    # ------------------------------------------------------------------

    def _draw_debug_overlay(self, gold, base_hp, base_max_hp,
                            round_number, tower_count, enemy_count):
        """Draw debug info panel in the top-right area."""
        sw = self.config["screen"]["width"]
        lines = [
            "DEBUG [F3]",
            f"Round: {round_number}",
            f"Gold: {gold}",
            f"HP: {base_hp}/{base_max_hp}",
            f"Towers: {tower_count}",
            f"Enemies: {enemy_count}",
            "",
            "[G] +500 gold",
            "[K] Kill all enemies",
            "[U] Unlock all towers",
        ]
        line_h = 16
        panel_w = 160
        panel_h = len(lines) * line_h + 12
        px = sw - panel_w - 8
        py = 100

        tinted_dbg = self._tinted_panel(panel_w, panel_h, (15, 8, 8))
        if tinted_dbg is not None:
            self.screen.blit(tinted_dbg, (px, py))
        else:
            pygame.draw.rect(self.screen, (15, 8, 8),
                             (px, py, panel_w, panel_h), border_radius=4)
        pygame.draw.rect(self.screen, (255, 80, 80),
                         (px, py, panel_w, panel_h), 1, border_radius=4)

        for i, line in enumerate(lines):
            c = (255, 100, 100) if i == 0 else (220, 220, 200)
            txt = self.font_tiny.render(line, True, c)
            self.screen.blit(txt, (px + 8, py + 6 + i * line_h))
