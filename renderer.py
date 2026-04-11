"""Renderer module.

Draws the game using sprite assets loaded by AssetLoader. Terrain tiles,
towers, enemies, soldiers, projectiles, and UI elements are all rendered
via ``blit()`` with pre-scaled sprites — no manual ``pygame.draw`` shapes
for game entities.

Game logic stays in other modules; this module only paints.
"""

import math
import os
import random
import pygame
from enums import TowerType, EnemyType
from effects import Effects
from asset_loader import AssetLoader
from rendering.draw_entities import RendererEntitiesMixin
from rendering.draw_hud import RendererHudMixin
from rendering.draw_overlays import RendererOverlaysMixin


_COLORKEY = (255, 0, 255)


class _SafeFont:
    """Wrapper around ``pygame.font.Font`` that avoids per-pixel alpha.

    On macOS retina, ``font.render`` with anti-aliasing produces SRCALPHA
    surfaces whose transparent pixels display as opaque rectangles. This
    wrapper renders text with an explicit background colour and applies
    ``set_colorkey`` so transparency relies on colorkey instead.
    """

    def __init__(self, font):
        self._font = font

    def render(self, text, antialias=True, color=(255, 255, 255),
               background=None):
        """Render text using colorkey transparency."""
        bg = background if background is not None else _COLORKEY
        surf = self._font.render(text, antialias, color, bg)
        if background is None:
            surf.set_colorkey(_COLORKEY)
        return surf

    def __getattr__(self, name):
        return getattr(self._font, name)


class Renderer(RendererEntitiesMixin, RendererHudMixin, RendererOverlaysMixin):
    """Handles all game rendering using sprite-based assets.

    Attributes:
        screen: Pygame display surface.
        config: Game configuration dictionary.
        tile_size: Tile size in pixels.
        assets: AssetLoader instance with cached sprites.
        anim_tick: Frame counter for animations.
        particles: List of active particle dicts.
        damage_numbers: List of floating damage number dicts.
        grass_cache: Pre-rendered terrain surface.
    """

    def __init__(self, screen, config):
        """Initialize the renderer and load all sprite assets.

        Args:
            screen: Pygame display surface.
            config: Game configuration dictionary.
        """
        self.screen = screen
        self.config = config
        self.tile_size = config["grid"]["tile_size"]
        pygame.font.init()

        assets_dir = os.path.join(os.path.dirname(__file__), "assets")
        self.assets = AssetLoader(assets_dir, self.tile_size)

        self.font_tiny = _SafeFont(self.assets.get_font(13))
        self.font_small = _SafeFont(self.assets.get_font(16))
        self.font_medium = _SafeFont(self.assets.get_font(20, bold=True))
        self.font_large = _SafeFont(self.assets.get_font(36, bold=True))
        self.font_title = _SafeFont(self.assets.get_font(50, bold=True))
        self.font_dmg = _SafeFont(self.assets.get_font(18, bold=True))

        self.anim_tick = 0
        self.effects = Effects()
        self.particles = []
        self.damage_numbers = []
        self.grass_cache = None
        self._cached_grid = None
        self._base_wp = None

    def invalidate_grass_cache(self):
        """Force the grass/terrain cache to be rebuilt next frame."""
        self.grass_cache = None
        self._cached_grid = None

    def add_damage_number(self, x, y, amount, color=(255, 255, 80)):
        """Add a floating damage number at the given position."""
        self.damage_numbers.append({
            "x": x, "y": float(y), "amount": amount,
            "timer": 0.8, "color": color
        })

    def spawn_effect(self, x, y, kind="explosion", size=64):
        """Spawn a sprite animation at the given position."""
        self.effects.spawn(x, y, kind, size)

    def add_particles(self, x, y, count, color, speed=2.0):
        """Spawn particle effects at a position."""
        for _ in range(count):
            angle = random.uniform(0, math.pi * 2)
            spd = random.uniform(speed * 0.3, speed)
            self.particles.append({
                "x": float(x), "y": float(y),
                "vx": math.cos(angle) * spd,
                "vy": math.sin(angle) * spd,
                "timer": random.uniform(0.2, 0.6),
                "color": color,
                "size": random.randint(2, 4)
            })

    def _update_vfx(self, dt):
        """Update particle and damage number lifetimes."""
        alive = []
        for p in self.particles:
            p["timer"] -= dt
            if p["timer"] > 0:
                p["x"] += p["vx"]
                p["y"] += p["vy"]
                p["vy"] += 0.1
                alive.append(p)
        self.particles = alive

        alive_dmg = []
        for d in self.damage_numbers:
            d["timer"] -= dt
            d["y"] -= 1.2
            if d["timer"] > 0:
                alive_dmg.append(d)
        self.damage_numbers = alive_dmg

    def _draw_vfx(self):
        """Draw particles using sprite assets and floating damage numbers."""
        _PARTICLE_MAP = {
            (200, 60, 60): "fire",
            (255, 140, 40): "flame",
            (180, 80, 30): "smoke",
            (255, 215, 0): "star",
        }
        for p in self.particles:
            size = max(4, int(p["size"] * 3 * max(0.2, p["timer"])))
            key = _PARTICLE_MAP.get(p["color"], "spark")
            sprite = self.assets.particles.get(key)
            if sprite is not None:
                scaled = pygame.transform.scale(sprite, (size, size))
                scaled.set_colorkey((255, 0, 255))
                self.screen.blit(scaled,
                                 (int(p["x"]) - size // 2,
                                  int(p["y"]) - size // 2))
            else:
                pygame.draw.circle(self.screen, p["color"],
                                   (int(p["x"]), int(p["y"])),
                                   max(1, size // 2))

        for d in self.damage_numbers:
            text = self.font_dmg.render(str(d["amount"]), True, d["color"])
            self.screen.blit(text, (int(d["x"]) - text.get_width() // 2,
                                    int(d["y"])))

    # ------------------------------------------------------------------
    # Main draw
    # ------------------------------------------------------------------

    def draw_game(self, game_map, towers, enemies, soldiers, projectiles,
                  gold, base_hp, base_max_hp, round_number,
                  selected_tower_type, hover_pos, selected_tower,
                  tower_unlocks=None, round_timer=0.0, game_speed=1,
                  base_level=1, selected_base=False, show_skip=False,
                  base_armor=0, base_wp=None, selected_build_spot=None,
                  debug_mode=False):
        """Draw the complete game frame."""
        self.anim_tick += 1
        self._base_wp = base_wp
        dt = 1.0 / max(self.config["screen"]["fps"], 30)
        self.effects.update(dt)
        self._update_vfx(dt)

        self._draw_map(game_map)
        self._draw_spawn_portal(game_map)
        self._draw_base_castle(game_map, base_hp, base_max_hp, base_level,
                               selected_base)
        self._draw_build_spots(game_map, hover_pos, selected_tower_type, gold)

        for tower in towers:
            self._draw_shadow(tower.pixel_x, tower.pixel_y + 8,
                              self.tile_size // 3)
        self._draw_towers(towers)

        self._draw_projectiles(projectiles)
        self._draw_attack_beams(towers)

        for enemy in enemies:
            if enemy.is_alive:
                self._draw_shadow(int(enemy.x), int(enemy.y) + 8, 9)
        self._draw_enemies(enemies)
        self._draw_soldiers(soldiers)

        if selected_tower is not None:
            self._draw_tower_range(selected_tower)

        self.effects.draw(self.screen, self.assets)
        self._draw_vfx()

        self._draw_ui_panel(gold, base_hp, base_max_hp, round_number,
                            selected_tower_type, selected_tower,
                            tower_unlocks, round_timer, game_speed,
                            base_level, selected_base, show_skip,
                            base_armor)

        if selected_build_spot is not None:
            self._draw_build_menu(selected_build_spot, gold, tower_unlocks)

        if debug_mode:
            self._draw_debug_overlay(gold, base_hp, base_max_hp,
                                     round_number, len(towers), len(enemies))

    # ------------------------------------------------------------------
    # Map (cached terrain blit)
    # ------------------------------------------------------------------

    def _draw_map(self, game_map):
        """Draw the tile grid with KR-style trench paths."""
        ts = self.tile_size
        cache_key = (id(game_map), len(game_map.locked_spots),
                     len(game_map.build_spots))
        if self.grass_cache is None or self._cached_grid != cache_key:
            self._cached_grid = cache_key
            w_px = game_map.cols * ts
            h_px = game_map.rows * ts
            self.grass_cache = pygame.Surface((w_px, h_px))

            build_set = set(game_map.build_spots)
            locked_set = set(game_map.locked_spots)
            path_set = set()
            for r in range(game_map.rows):
                for c in range(game_map.cols):
                    if game_map.grid[r][c] == 1:
                        path_set.add((c, r))

            for row in range(game_map.rows):
                for col in range(game_map.cols):
                    px = col * ts
                    py = row * ts
                    self.grass_cache.blit(
                        self.assets.terrain["grass"], (px, py))

            edge = 5
            dirt = (175, 140, 90)
            dirt_dark = (145, 115, 70)
            shadow = (120, 95, 55)
            highlight = (195, 165, 115)

            for col, row in path_set:
                px, py = col * ts, row * ts
                self.grass_cache.fill(dirt, (px, py, ts, ts))

                top = (col, row - 1) in path_set
                bot = (col, row + 1) in path_set
                left = (col - 1, row) in path_set
                right = (col + 1, row) in path_set

                if not top:
                    pygame.draw.rect(self.grass_cache, shadow,
                                     (px, py, ts, edge))
                    pygame.draw.line(self.grass_cache, (90, 130, 55),
                                     (px, py), (px + ts, py), 2)
                if not bot:
                    pygame.draw.rect(self.grass_cache, highlight,
                                     (px, py + ts - edge, ts, edge))
                    pygame.draw.line(self.grass_cache, (90, 130, 55),
                                     (px, py + ts - 1),
                                     (px + ts, py + ts - 1), 2)
                if not left:
                    pygame.draw.rect(self.grass_cache, shadow,
                                     (px, py, edge, ts))
                    pygame.draw.line(self.grass_cache, (90, 130, 55),
                                     (px, py), (px, py + ts), 2)
                if not right:
                    pygame.draw.rect(self.grass_cache, highlight,
                                     (px + ts - edge, py, edge, ts))
                    pygame.draw.line(self.grass_cache, (90, 130, 55),
                                     (px + ts - 1, py),
                                     (px + ts - 1, py + ts), 2)

                rng = __import__('random').Random(col * 31 + row * 17)
                for _ in range(4):
                    gx = px + rng.randint(edge, ts - edge - 1)
                    gy = py + rng.randint(edge, ts - edge - 1)
                    pygame.draw.circle(self.grass_cache, dirt_dark,
                                       (gx, gy), 1)

            for row in range(game_map.rows):
                for col in range(game_map.cols):
                    if (col, row) in path_set:
                        continue
                    px = col * ts
                    py = row * ts
                    is_build = (col, row) in build_set
                    is_locked = (col, row) in locked_set
                    if is_build or is_locked:
                        key = ("platform_locked" if is_locked
                               else "platform")
                        self.grass_cache.blit(
                            self.assets.terrain[key], (px, py))
                    else:
                        near_path = any(
                            (col + dc, row + dr) in path_set
                            for dc in range(-1, 2)
                            for dr in range(-1, 2)
                            if dc or dr
                        )
                        if near_path:
                            continue
                        deco = self.assets.get_decoration(col, row)
                        dx = px + (ts - deco.get_width()) // 2
                        dy = py + (ts - deco.get_height()) // 2
                        self.grass_cache.blit(deco, (dx, dy))
        self.screen.blit(self.grass_cache, (0, 0))

    # ------------------------------------------------------------------
    # Spawn portal (animated)
    # ------------------------------------------------------------------

    def _draw_spawn_portal(self, game_map):
        """Draw a portal sprite at the enemy spawn point with pulse animation."""
        waypoints = game_map.get_path_pixel_waypoints()
        if not waypoints:
            return
        sx, sy = waypoints[0]
        t = self.anim_tick * 0.06

        portal = self.assets.particles.get("portal")
        if portal is None:
            return

        pulse = 1.0 + math.sin(t * 2) * 0.08
        pw = int(portal.get_width() * pulse)
        ph = int(portal.get_height() * pulse)
        scaled = pygame.transform.scale(portal, (pw, ph))
        scaled.set_colorkey((255, 0, 255))

        angle = (self.anim_tick * 2) % 360
        rotated = pygame.transform.rotate(scaled, angle)
        rotated.set_colorkey((255, 0, 255))
        rw, rh = rotated.get_size()
        self.screen.blit(rotated, (sx - rw // 2, sy - rh // 2))

        glow_r = int(self.tile_size * 0.18 * pulse)
        pygame.draw.circle(self.screen, (160, 60, 220), (sx, sy), glow_r, 2)

    # ------------------------------------------------------------------
    # Base castle (sprite-based)
    # ------------------------------------------------------------------

    def _draw_base_castle(self, game_map, base_hp, base_max_hp,
                          base_level=1, selected_base=False):
        """Draw the castle sprite at the base with HP bar and selection ring."""
        waypoints = game_map.get_path_pixel_waypoints()
        if not waypoints:
            return
        bx, by = waypoints[-1]
        ts = self.tile_size

        if selected_base:
            sel_r = int(ts * 1.0)
            pulse = abs(math.sin(self.anim_tick * 0.08))
            brightness = int(180 + pulse * 75)
            ring_c = (brightness, min(255, int(brightness * 0.86)),
                      int(80 + pulse * 40))
            pygame.draw.circle(self.screen, ring_c, (bx, by), sel_r, 3)

        castle = self.assets.ui.get("castle")
        if castle is not None:
            cw, ch = castle.get_size()
            self.screen.blit(castle, (bx - cw // 2, by - ch // 2))
            castle_w = cw
        else:
            castle_w = int(ts * 1.1)

        ratio = base_hp / base_max_hp if base_max_hp > 0 else 0
        bar_w = castle_w + 8
        bar_h = 7
        bar_x = bx - bar_w // 2
        bar_y = by - castle_w // 2 - 16
        self._draw_health_bar(bar_x, bar_y, bar_w, bar_h, ratio)

        lvl_text = self.font_tiny.render(f"Lv{base_level}", True,
                                         (255, 220, 100))
        self.screen.blit(lvl_text,
                         (bx - lvl_text.get_width() // 2, bar_y - 14))

    # ------------------------------------------------------------------
    # Build spots
    # ------------------------------------------------------------------

    def _draw_build_spots(self, game_map, hover_pos,
                          selected_tower_type, gold=0):
        """Draw platform sprites on valid and locked build spots.

        Args:
            game_map: GameMap instance.
            hover_pos: Current hovered grid (col, row) or None.
            selected_tower_type: Currently selected TowerType or None.
            gold: Current player gold (for locked spot affordability).
        """
        ts = self.tile_size
        slot_cost = self.config["gameplay"].get("slot_unlock_cost", 0)
        platform = self.assets.terrain.get("platform")
        platform_locked = self.assets.terrain.get("platform_locked")

        for col, row in game_map.build_spots:
            is_hover = (selected_tower_type is not None
                        and hover_pos is not None
                        and hover_pos == (col, row))
            if is_hover:
                px_x = col * ts
                px_y = row * ts
                pygame.draw.rect(self.screen, (120, 255, 120),
                                 (px_x + 1, px_y + 1, ts - 2, ts - 2),
                                 3, border_radius=6)

        for col, row in game_map.locked_spots:
            is_hover = (hover_pos is not None and hover_pos == (col, row))
            if is_hover:
                px_x = col * ts
                px_y = row * ts
                cx = col * ts + ts // 2
                cy = row * ts + ts // 2
                can_afford = gold >= slot_cost
                border_c = (255, 215, 80) if can_afford else (120, 100, 60)
                pygame.draw.rect(self.screen, border_c,
                                 (px_x + 1, px_y + 1, ts - 2, ts - 2),
                                 3, border_radius=6)
                cost_c = (255, 215, 50) if can_afford else (160, 130, 70)
                cost_txt = self.font_small.render(f"{slot_cost}g", True,
                                                  cost_c)
                self.screen.blit(cost_txt,
                                 cost_txt.get_rect(center=(cx, cy + ts // 4)))

    # ------------------------------------------------------------------
    # Shadows
    # ------------------------------------------------------------------

    def _draw_shadow(self, cx, cy, radius):
        """Draw an elliptical shadow beneath an entity."""
        pygame.draw.ellipse(self.screen, (30, 30, 20),
                            (cx - radius, cy - radius // 4,
                             radius * 2, radius // 2), 0)
