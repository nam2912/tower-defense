"""Mixin for overlay screens: menu, pause, round complete/fail, game over."""

import math
import random
import pygame
from enums import TowerType


class RendererOverlaysMixin:
    """Mixin providing overlay screens: menu, pause, round failed, buttons."""

    # ------------------------------------------------------------------
    # Overlay screens
    # ------------------------------------------------------------------

    def _draw_overlay_bg(self, brightness=90):
        """Darken the screen while keeping the map visible underneath.

        Uses ``BLEND_RGB_MULT`` to multiply existing pixel colours by a
        tint value, avoiding alpha-blending entirely (which is unreliable
        on macOS retina displays).

        Args:
            brightness: 0-255 tint level. Lower = darker.
        """
        sw = self.config["screen"]["width"]
        sh = self.config["screen"]["height"]
        tint = pygame.Surface((sw, sh))
        b = max(20, min(brightness, 200))
        tint.fill((b, b, b))
        self.screen.blit(tint, (0, 0),
                         special_flags=pygame.BLEND_RGB_MULT)

    def _tinted_panel(self, width, height, tint):
        """Return a panel_bg sprite scaled and tinted to a dark colour.

        Uses ``BLEND_RGB_MULT`` to multiply the light Kenney panel sprite
        by a tint colour, producing a dark-themed surface that keeps the
        sprite's shading/highlight detail. Falls back to a plain rect if
        the sprite is missing.

        Args:
            width: Target width in pixels.
            height: Target height in pixels.
            tint: (r, g, b) multiplier — lower values = darker.

        Returns:
            pygame.Surface or None if the sprite is unavailable.
        """
        panel = self.assets.ui.get("panel_bg")
        if panel is None:
            return None
        scaled = pygame.transform.scale(panel, (width, height))
        scaled.fill(tint, special_flags=pygame.BLEND_RGB_MULT)
        scaled.set_colorkey((255, 0, 255))
        return scaled

    def _draw_decorative_frame(self, rect, border_color, fill_color):
        """Draw a decorative frame using a tinted panel sprite."""
        tinted = self._tinted_panel(rect.width, rect.height, fill_color)
        if tinted is not None:
            self.screen.blit(tinted, rect.topleft)
        else:
            shadow = rect.inflate(4, 4).move(2, 2)
            pygame.draw.rect(self.screen, (15, 12, 10), shadow,
                             border_radius=14)
            pygame.draw.rect(self.screen, fill_color, rect,
                             border_radius=12)
        pygame.draw.rect(self.screen, border_color, rect, 3,
                         border_radius=12)
        inner = rect.inflate(-8, -8)
        lighter = tuple(min(255, c + 30) for c in border_color)
        pygame.draw.rect(self.screen, lighter, inner, 1,
                         border_radius=10)

    def _blit_ui_btn(self, btn_key, rect, hovering=False, tint=None):
        """Blit a UI button sprite scaled and optionally tinted.

        Args:
            btn_key: Key in assets.ui (e.g. ``"btn_green"``).
            rect: Target ``pygame.Rect``.
            hovering: Whether mouse is hovering (brightens sprite).
            tint: Optional (r, g, b) multiplier to darken the sprite.
        """
        sprite = self.assets.ui.get(btn_key)
        if sprite is not None:
            scaled = pygame.transform.scale(sprite,
                                            (rect.width, rect.height))
            if tint is not None:
                scaled.fill(tint, special_flags=pygame.BLEND_RGB_MULT)
            scaled.set_colorkey((255, 0, 255))
            self.screen.blit(scaled, rect.topleft)
        else:
            pygame.draw.rect(self.screen, (45, 45, 60), rect, border_radius=6)
            pygame.draw.rect(self.screen, (140, 140, 160), rect, 2,
                             border_radius=6)

    def _draw_button(self, rect, text, bg_color, hover_color, border_color):
        """Draw a styled button using sprite assets with hover detection.

        Returns:
            True if the mouse is hovering over this button.
        """
        mouse_pos = pygame.mouse.get_pos()
        hovering = rect.collidepoint(mouse_pos)

        btn_key = "btn_green"
        if border_color[0] > 200 and border_color[1] < 100:
            btn_key = "btn_red"
        elif border_color[0] > 200 and border_color[1] > 150:
            btn_key = "btn_yellow"
        elif bg_color[2] > bg_color[0]:
            btn_key = "btn_blue"
        elif bg_color[0] < 60 and bg_color[1] < 60:
            btn_key = "btn_grey"

        self._blit_ui_btn(btn_key, rect, hovering)

        btn_text = self.font_medium.render(text, True, (255, 255, 255))
        btn_text_rect = btn_text.get_rect(center=rect.center)
        shadow = self.font_medium.render(text, True, (0, 0, 0))
        self.screen.blit(shadow,
                         (btn_text_rect.x + 1, btn_text_rect.y + 1))
        self.screen.blit(btn_text, btn_text_rect)
        return hovering

    def draw_menu(self):
        """Draw the main menu screen."""
        sw = self.config["screen"]["width"]
        sh = self.config["screen"]["height"]
        self.anim_tick += 1

        for y in range(sh):
            ratio = y / sh
            r = int(18 + ratio * 12)
            g = int(14 + ratio * 10)
            b = int(28 + ratio * 18)
            pygame.draw.line(self.screen, (r, g, b), (0, y), (sw, y))

        star_rng = random.Random(42)
        for _ in range(50):
            sx = star_rng.randint(0, sw)
            sy = star_rng.randint(0, sh // 2)
            twinkle = abs(math.sin(self.anim_tick * 0.03 + sx * 0.1))
            brightness = int(90 + twinkle * 130)
            size = 1 if twinkle < 0.5 else 2
            warm = min(255, brightness + 20)
            pygame.draw.circle(self.screen, (warm, brightness,
                                             brightness - 10),
                               (sx, sy), size)

        frame = pygame.Rect(sw // 2 - 280, 110, 560, 420)
        self._draw_decorative_frame(frame, (150, 120, 60), (25, 20, 35))

        shadow = self.font_title.render("Tower Defense", True, (70, 45, 10))
        self.screen.blit(shadow, shadow.get_rect(center=(sw // 2 + 3, 173)))
        title = self.font_title.render("Tower Defense", True, (255, 215, 80))
        self.screen.blit(title, title.get_rect(center=(sw // 2, 170)))

        sub = self.font_medium.render(
            "Infinite rounds \u2014 How far can you go?", True, (200, 190, 170)
        )
        self.screen.blit(sub, sub.get_rect(center=(sw // 2, 225)))

        pygame.draw.line(self.screen, (130, 105, 55),
                         (sw // 2 - 160, 250), (sw // 2 + 160, 250), 1)

        pulse = int(abs(math.sin(self.anim_tick * 0.05)) * 40)
        start_color = (200 + min(pulse, 55), 180 + min(pulse, 75), 70)
        start_text = self.font_large.render(
            "Press SPACE to Start", True, start_color
        )
        self.screen.blit(start_text,
                         start_text.get_rect(center=(sw // 2, 310)))

        controls = [
            "[1-0] Select tower (10 types)  |  Click map to place",
            "Click tower/castle for radial upgrade & sell",
            "[ESC] Deselect  |  15 upgrade levels per tower!",
            "Speed & pause buttons in top-right corner",
        ]
        for i, line in enumerate(controls):
            ctrl_text = self.font_small.render(line, True, (150, 140, 120))
            self.screen.blit(ctrl_text,
                             ctrl_text.get_rect(center=(sw // 2, 380 + i * 24)))

    def draw_round_failed(self, round_number):
        """Draw the round failed overlay."""
        sw = self.config["screen"]["width"]
        sh = self.config["screen"]["height"]
        self.anim_tick += 1
        self._draw_overlay_bg(100)

        cx = sw // 2
        title_surf = self.font_large.render(
            "Base Destroyed!", True, (255, 80, 80))
        info_surf = self.font_medium.render(
            f"Round {round_number}", True, (200, 200, 200))
        max_w = max(title_surf.get_width(), info_surf.get_width())
        btn_w = 220
        frame_w = min(max(max_w + 60, btn_w + 60), sw - 40)
        frame_h = 240
        fy = sh // 2 - frame_h // 2

        frame = pygame.Rect(cx - frame_w // 2, fy, frame_w, frame_h)
        self._draw_decorative_frame(frame, (180, 60, 60), (30, 12, 12))

        self.screen.blit(title_surf,
                         title_surf.get_rect(center=(cx, fy + 38)))
        self.screen.blit(info_surf,
                         info_surf.get_rect(center=(cx, fy + 80)))

        retry_btn = pygame.Rect(cx - btn_w // 2, fy + 110, btn_w, 42)
        self._draw_button(retry_btn, "Retry [R]",
                          (140, 90, 30), (180, 120, 40), (220, 160, 60))

        restart_btn = pygame.Rect(cx - btn_w // 2, fy + 166, btn_w, 42)
        self._draw_button(restart_btn, "Restart",
                          (50, 50, 70), (70, 70, 90), (110, 110, 130))

    def draw_pause_overlay(self, music_muted=False, music_volume=0.3,
                           debug_mode=False):
        """Draw the pause/settings menu with a volume progress bar."""
        sw = self.config["screen"]["width"]
        sh = self.config["screen"]["height"]
        self._draw_overlay_bg(90)
        rects = self.get_settings_rects()
        mouse = pygame.mouse.get_pos()

        frame_w, frame_h = 360, 340
        fx = sw // 2 - frame_w // 2
        fy = sh // 2 - frame_h // 2
        frame = pygame.Rect(fx, fy, frame_w, frame_h)
        self._draw_decorative_frame(frame, (120, 120, 140), (35, 35, 50))

        title = self.font_title.render("PAUSED", True, (255, 255, 255))
        self.screen.blit(title,
                         title.get_rect(center=(sw // 2, fy + 40)))

        settings_label = self.font_medium.render("Settings", True,
                                                  (200, 200, 210))
        self.screen.blit(settings_label,
                         settings_label.get_rect(center=(sw // 2, fy + 85)))

        mute_r = rects["mute"]
        mute_hover = mute_r.collidepoint(mouse)
        btn_key = "btn_red" if music_muted else "btn_green"
        self._blit_ui_btn(btn_key, mute_r, mute_hover)
        mute_text = "Unmute" if music_muted else "Mute"
        mt = self.font_small.render(mute_text, True, (255, 255, 255))
        self.screen.blit(mt, mt.get_rect(center=mute_r.center))

        vol_lbl = self.font_tiny.render("Volume", True, (180, 180, 190))
        self.screen.blit(vol_lbl, (rects["vol_down"].x, fy + 133))

        for key in ("vol_down", "vol_up"):
            r = rects[key]
            hov = r.collidepoint(mouse)
            self._blit_ui_btn("btn_blue", r, hov)
            sym = "-" if key == "vol_down" else "+"
            st = self.font_medium.render(sym, True, (255, 255, 255))
            self.screen.blit(st, st.get_rect(center=r.center))

        bar_x = rects["vol_down"].right + 8
        bar_w = rects["vol_up"].left - bar_x - 8
        bar_y = rects["vol_down"].y + 4
        bar_h = rects["vol_down"].height - 8
        pygame.draw.rect(self.screen, (30, 30, 40),
                         (bar_x, bar_y, bar_w, bar_h), border_radius=4)
        fill_w = max(0, int(bar_w * music_volume))
        if fill_w > 0:
            fill_color = (80, 180, 80) if not music_muted else (120, 80, 80)
            pygame.draw.rect(self.screen, fill_color,
                             (bar_x, bar_y, fill_w, bar_h), border_radius=4)
        pygame.draw.rect(self.screen, (100, 100, 120),
                         (bar_x, bar_y, bar_w, bar_h), 1, border_radius=4)
        pct = self.font_tiny.render(
            f"{int(music_volume * 100)}%", True, (220, 220, 220))
        self.screen.blit(pct, pct.get_rect(center=(bar_x + bar_w // 2,
                                                    bar_y + bar_h // 2)))

        dbg_r = rects["debug"]
        dbg_hover = dbg_r.collidepoint(mouse)
        dbg_key = "btn_green" if debug_mode else "btn_yellow"
        self._blit_ui_btn(dbg_key, dbg_r, dbg_hover)
        check_label = "Debug: ON" if debug_mode else "Debug: OFF"
        dt_txt = self.font_small.render(check_label, True, (255, 255, 255))
        self.screen.blit(dt_txt, dt_txt.get_rect(center=dbg_r.center))

        if debug_mode:
            cheats = self.font_tiny.render(
                "[G] +500g  [K] Kill all  [U] Unlock",
                True, (255, 180, 100))
            self.screen.blit(cheats,
                             cheats.get_rect(center=(sw // 2, dbg_r.bottom + 18)))

        resume_r = rects["resume"]
        self._draw_button(resume_r, "Resume [ESC]",
                          (40, 100, 40), (60, 140, 60), (100, 200, 100))

    # ------------------------------------------------------------------
    # Button rect helpers (unchanged API)
    # ------------------------------------------------------------------

    def _get_centered_button_rect(self, y_top):
        """Get a centered button rectangle."""
        sw = self.config["screen"]["width"]
        btn_w, btn_h = 340, 50
        return pygame.Rect(sw // 2 - btn_w // 2, y_top, btn_w, btn_h)

    def get_tower_button_rects(self):
        """Get clickable rectangles for the bottom tower bar."""
        tower_types = [
            TowerType.FORTRESS, TowerType.ARCHER, TowerType.BARRACKS,
            TowerType.MAGE, TowerType.ARTILLERY, TowerType.FREEZE,
            TowerType.POISON, TowerType.BALLISTA, TowerType.TESLA,
            TowerType.NECROMANCER, TowerType.LASER,
        ]
        screen_w = self.config["screen"]["width"]
        screen_h = self.config["screen"]["height"]
        btn_size = 48
        gap = 5
        total_w = len(tower_types) * btn_size + (len(tower_types) - 1) * gap
        start_x = (screen_w - total_w) // 2
        bar_y = screen_h - btn_size - 12

        buttons = []
        for i, t_type in enumerate(tower_types):
            x = start_x + i * (btn_size + gap)
            rect = pygame.Rect(x, bar_y, btn_size, btn_size)
            buttons.append((t_type, rect))
        return buttons

    def get_upgrade_button_rect(self, tower):
        """Get the radial upgrade button rect above a tower."""
        cx, cy = tower.pixel_x, tower.pixel_y
        btn_w, btn_h = 48, 40
        ring_r = self.tile_size // 2 + 20
        return pygame.Rect(cx - btn_w // 2, cy - ring_r - btn_h // 2,
                           btn_w, btn_h)

    def get_sell_button_rect(self, tower):
        """Get the radial sell button rect below a tower."""
        cx, cy = tower.pixel_x, tower.pixel_y
        btn_w, btn_h = 48, 40
        ring_r = self.tile_size // 2 + 20
        return pygame.Rect(cx - btn_w // 2, cy + ring_r - btn_h // 2,
                           btn_w, btn_h)

    def get_base_upgrade_button_rect(self):
        """Get the radial upgrade button rect above the base castle."""
        wp = getattr(self, "_base_wp", None)
        if wp is None:
            return None
        bx, by = wp
        btn_w, btn_h = 48, 40
        ring_r = self.tile_size // 2 + 20
        return pygame.Rect(bx - btn_w // 2, by - ring_r - btn_h // 2,
                           btn_w, btn_h)

    def get_retry_button_rect(self):
        """Get the 'Retry' button rectangle."""
        sh = self.config["screen"]["height"]
        return self._get_centered_button_rect(sh // 2 + 10)

    def get_full_restart_button_rect(self):
        """Get the 'Full Restart' button on round failed screen."""
        sh = self.config["screen"]["height"]
        return self._get_centered_button_rect(sh // 2 + 80)

    def get_speed_button_rect(self):
        """Get the speed toggle button rectangle (top-right)."""
        screen_w = self.config["screen"]["width"]
        return pygame.Rect(screen_w - 90, 8, 40, 28)

    def get_pause_button_rect(self):
        """Get the pause button rectangle (top-right corner)."""
        screen_w = self.config["screen"]["width"]
        return pygame.Rect(screen_w - 44, 8, 36, 28)

    def get_skip_button_rect(self):
        """Get the skip button rectangle (below speed/pause buttons)."""
        screen_w = self.config["screen"]["width"]
        return pygame.Rect(screen_w - 90, 60, 80, 30)

    def get_settings_rects(self):
        """Get clickable rectangles for the pause/settings menu."""
        sw = self.config["screen"]["width"]
        sh = self.config["screen"]["height"]
        cx = sw // 2
        fy = sh // 2 - 170
        return {
            "mute": pygame.Rect(cx - 50, fy + 110, 100, 30),
            "vol_down": pygame.Rect(cx - 130, fy + 150, 36, 28),
            "vol_up": pygame.Rect(cx + 95, fy + 150, 36, 28),
            "debug": pygame.Rect(cx - 70, fy + 195, 140, 30),
            "resume": pygame.Rect(cx - 120, fy + 270, 240, 50),
        }
