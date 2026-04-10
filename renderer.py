"""Renderer module.

Draws polished 2D sprites, environmental detail, health bars,
projectile trails, floating damage numbers, and a refined UI.
All drawing functions receive the surface and data as parameters.

Design patterns: Separation of Concerns (Model-View).
See REFERENCES.md for full citations.
"""

import math
import random
import pygame
from enums import TowerType, EnemyType


class Renderer:
    """Handles all game rendering and UI drawing.

    Attributes:
        screen: Pygame display surface.
        config: Game configuration dictionary.
        tile_size: Tile size in pixels.
        anim_tick: Frame counter for animations.
        particles: List of active particle dicts.
        damage_numbers: List of floating damage number dicts.
        grass_cache: Pre-rendered grass surface.
    """

    def __init__(self, screen, config):
        """Initialize the renderer.

        Args:
            screen: Pygame display surface.
            config: Game configuration dictionary.
        """
        self.screen = screen
        self.config = config
        self.tile_size = config["grid"]["tile_size"]
        pygame.font.init()
        self.font_tiny = pygame.font.SysFont("Arial", 11)
        self.font_small = pygame.font.SysFont("Arial", 14)
        self.font_medium = pygame.font.SysFont("Arial", 20, bold=True)
        self.font_large = pygame.font.SysFont("Arial", 36, bold=True)
        self.font_title = pygame.font.SysFont("Arial", 52, bold=True)
        self.font_dmg = pygame.font.SysFont("Arial", 16, bold=True)
        self.anim_tick = 0
        self.particles = []
        self.damage_numbers = []
        self.grass_cache = None
        self._cached_grid = None
        self._base_wp = None

    def add_damage_number(self, x, y, amount, color=(255, 255, 80)):
        """Add a floating damage number at the given position.

        Args:
            x: X pixel position.
            y: Y pixel position.
            amount: Damage amount to display.
            color: RGB color tuple.
        """
        self.damage_numbers.append({
            "x": x, "y": float(y), "amount": amount,
            "timer": 0.8, "color": color
        })

    def add_particles(self, x, y, count, color, speed=2.0):
        """Spawn particle effects at a position.

        Args:
            x: X pixel position.
            y: Y pixel position.
            count: Number of particles.
            color: Base RGB color.
            speed: Particle speed.
        """
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

    def _update_particles(self, dt):
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

    def _draw_particles_and_numbers(self):
        """Draw particles and floating damage numbers."""
        for p in self.particles:
            alpha = min(255, int(p["timer"] * 500))
            size = max(1, p["size"] - int((0.6 - p["timer"]) * 3))
            pygame.draw.circle(self.screen, p["color"],
                               (int(p["x"]), int(p["y"])), size)

        for d in self.damage_numbers:
            alpha_ratio = min(1.0, d["timer"] / 0.3)
            c = d["color"]
            text = self.font_dmg.render(str(d["amount"]), True, c)
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
                  base_armor=0, base_wp=None):
        """Draw the complete game frame."""
        self.anim_tick += 1
        self._base_wp = base_wp
        dt = 1.0 / max(self.config["screen"]["fps"], 30)
        self._update_particles(dt)
        colors = self.config["colors"]

        self._draw_map(game_map, colors)
        self._draw_spawn_portal(game_map)
        self._draw_base_castle(game_map, base_hp, base_max_hp, base_level,
                               selected_base)
        self._draw_build_spots(game_map, colors, hover_pos, selected_tower_type)

        for tower in towers:
            self._draw_tower_shadow(tower)
        self._draw_towers(towers, colors)

        self._draw_projectiles(projectiles)

        for enemy in enemies:
            if enemy.is_alive:
                self._draw_shadow(int(enemy.x), int(enemy.y) + 8, 9)
        self._draw_enemies(enemies, colors)
        self._draw_soldiers(soldiers, colors)

        if selected_tower is not None:
            self._draw_tower_range(selected_tower)

        self._draw_particles_and_numbers()

        self._draw_ui_panel(gold, base_hp, base_max_hp, round_number,
                            selected_tower_type, selected_tower, colors,
                            tower_unlocks, round_timer, game_speed,
                            base_level, selected_base, show_skip,
                            base_armor)

    # ------------------------------------------------------------------
    # Map
    # ------------------------------------------------------------------

    def _draw_map(self, game_map, colors):
        """Draw the tile grid with textured grass and detailed path."""
        ts = self.tile_size
        if (self.grass_cache is None
                or self._cached_grid != id(game_map)):
            self._cached_grid = id(game_map)
            self.grass_cache = pygame.Surface(
                (game_map.cols * ts, game_map.rows * ts)
            )
            build_set = set(game_map.build_spots)
            for row in range(game_map.rows):
                for col in range(game_map.cols):
                    if game_map.grid[row][col] == 1:
                        self._draw_path_tile(self.grass_cache,
                                             col, row, game_map)
                    else:
                        self._draw_grass_tile(self.grass_cache,
                                              col, row, ts)
                        is_build = (col, row) in build_set
                        if is_build:
                            self._draw_build_platform(
                                self.grass_cache, col, row, ts)
                        else:
                            self._draw_terrain_decoration(
                                self.grass_cache, col, row, ts)
        self.screen.blit(self.grass_cache, (0, 0))

    def _draw_grass_tile(self, surface, col, row, ts):
        """Draw a lush Kingdom-Rush-style grass tile with warm tones."""
        rect = pygame.Rect(col * ts, row * ts, ts, ts)
        rng = random.Random(col * 1000 + row)
        base_g = 135 + (col * 7 + row * 13) % 25
        base_color = (55 + (col + row) % 15,
                      base_g,
                      35 + (col * 3 + row * 2) % 12)
        pygame.draw.rect(surface, base_color, rect)

        lighter = (min(255, base_color[0] + 8),
                   min(255, base_color[1] + 10),
                   min(255, base_color[2] + 6))
        hl_rect = pygame.Rect(col * ts + 3, row * ts + 3,
                               ts // 2 - 4, ts // 2 - 4)
        pygame.draw.rect(surface, lighter, hl_rect, border_radius=4)

        for _ in range(8):
            gx = col * ts + rng.randint(3, ts - 3)
            gy = row * ts + rng.randint(3, ts - 3)
            blade_h = rng.randint(4, 10)
            sway = rng.randint(-3, 3)
            g_val = rng.randint(110, 190)
            blade_c = (30 + rng.randint(0, 25), g_val, 20 + rng.randint(0, 15))
            pygame.draw.line(surface, blade_c,
                             (gx, gy), (gx + sway, gy - blade_h), 1)

        if rng.random() < 0.25:
            fx = col * ts + rng.randint(8, ts - 8)
            fy = row * ts + rng.randint(8, ts - 8)
            flower_colors = [(255, 220, 80), (255, 160, 100), (220, 180, 255),
                             (255, 200, 200), (255, 255, 180)]
            fc = rng.choice(flower_colors)
            pygame.draw.circle(surface, fc, (fx, fy), 2)
            pygame.draw.circle(surface, (255, 255, 220), (fx, fy), 1)

        edge_c = (max(0, base_color[0] - 10),
                  max(0, base_color[1] - 12),
                  max(0, base_color[2] - 8))
        pygame.draw.rect(surface, edge_c, rect, 1)

    def _draw_path_tile(self, surface, col, row, game_map):
        """Draw a warm cobblestone path tile with depth and edges."""
        ts = self.tile_size
        rect = pygame.Rect(col * ts, row * ts, ts, ts)
        pygame.draw.rect(surface, (175, 148, 115), rect)

        inner = pygame.Rect(col * ts + 2, row * ts + 2, ts - 4, ts - 4)
        pygame.draw.rect(surface, (160, 135, 100), inner)

        hl_rect = pygame.Rect(col * ts + 3, row * ts + 3, ts - 6, ts // 3)
        pygame.draw.rect(surface, (168, 143, 108), hl_rect, border_radius=4)

        rng = random.Random(col * 2000 + row)
        for _ in range(6):
            px = col * ts + rng.randint(5, ts - 5)
            py = row * ts + rng.randint(5, ts - 5)
            ps = rng.randint(2, 5)
            stone_c = rng.randint(120, 155)
            pygame.draw.circle(surface,
                               (stone_c + 10, stone_c, stone_c - 15),
                               (px, py), ps)
            pygame.draw.circle(surface,
                               (stone_c - 15, stone_c - 25, stone_c - 35),
                               (px, py), ps, 1)

        has_top = (row > 0 and game_map.grid[row - 1][col] != 1)
        has_bot = (row < game_map.rows - 1
                   and game_map.grid[row + 1][col] != 1)
        has_left = (col > 0 and game_map.grid[row][col - 1] != 1)
        has_right = (col < game_map.cols - 1
                     and game_map.grid[row][col + 1] != 1)
        edge_dark = (110, 85, 55)
        edge_light = (195, 175, 145)
        edge_w = 3
        if has_top:
            pygame.draw.line(surface, edge_dark,
                             (col * ts, row * ts),
                             (col * ts + ts, row * ts), edge_w)
        if has_bot:
            pygame.draw.line(surface, edge_light,
                             (col * ts, row * ts + ts - 1),
                             (col * ts + ts, row * ts + ts - 1), 2)
        if has_left:
            pygame.draw.line(surface, edge_dark,
                             (col * ts, row * ts),
                             (col * ts, row * ts + ts), edge_w)
        if has_right:
            pygame.draw.line(surface, edge_light,
                             (col * ts + ts - 1, row * ts),
                             (col * ts + ts - 1, row * ts + ts), 2)

    def _draw_build_platform(self, surface, col, row, ts):
        """Draw a warm stone platform with metallic rivets on buildable tiles."""
        cx = col * ts + ts // 2
        cy = row * ts + ts // 2
        pw, ph = ts - 10, ts - 10
        px, py = cx - pw // 2, cy - ph // 2

        shadow_c = (45, 55, 30)
        pygame.draw.rect(surface, shadow_c,
                         (px, py + 2, pw, ph), border_radius=5)

        pygame.draw.rect(surface, (150, 135, 105),
                         (px, py, pw, ph), border_radius=5)

        hl_rect = pygame.Rect(px + 2, py + 2, pw - 4, ph // 2 - 2)
        pygame.draw.rect(surface, (162, 148, 118), hl_rect, border_radius=4)

        pygame.draw.rect(surface, (110, 95, 70),
                         (px, py, pw, ph), 2, border_radius=5)

        rivet_c = (185, 170, 140)
        rivet_hl = (210, 200, 175)
        for dx, dy in [(5, 5), (pw - 6, 5), (5, ph - 6), (pw - 6, ph - 6)]:
            pygame.draw.circle(surface, rivet_c, (px + dx, py + dy), 3)
            pygame.draw.circle(surface, rivet_hl, (px + dx - 1, py + dy - 1), 1)

    def _draw_terrain_decoration(self, surface, col, row, ts):
        """Draw mountains, trees, rocks, or bushes on non-buildable tiles."""
        rng = random.Random(col * 7919 + row * 6271)
        deco_type = rng.randint(0, 12)

        cx = col * ts + ts // 2
        cy = row * ts + ts // 2

        if deco_type <= 2:
            mh = rng.randint(ts // 3, ts // 2)
            mw = rng.randint(ts // 2, ts - 6)
            base_y = cy + ts // 4
            peak_y = base_y - mh
            peak_x = cx + rng.randint(-4, 4)
            left_x = cx - mw // 2
            right_x = cx + mw // 2
            mc = rng.randint(90, 120)
            outline = (mc - 35, mc - 45, mc - 50)
            mountain_pts = [(left_x, base_y), (peak_x, peak_y),
                            (right_x, base_y)]
            pygame.draw.polygon(surface, outline, mountain_pts)
            pygame.draw.polygon(surface, (mc + 5, mc - 5, mc - 15),
                                mountain_pts)
            hl_c = (min(255, mc + 12), min(255, mc + 2), max(0, mc - 8))
            hl_pts = [(peak_x, peak_y),
                      (peak_x + mw // 4, base_y),
                      (right_x, base_y)]
            pygame.draw.polygon(surface, hl_c, hl_pts)
            snow_y = peak_y + mh // 4
            pygame.draw.polygon(surface, (235, 240, 250), [
                (cx - mw // 5, snow_y),
                (peak_x, peak_y),
                (cx + mw // 5, snow_y)
            ])
            pygame.draw.polygon(surface, (210, 215, 225), [
                (cx - mw // 5, snow_y),
                (peak_x, peak_y),
                (cx + mw // 5, snow_y)
            ], 1)
        elif deco_type <= 5:
            trunk_h = rng.randint(12, 20)
            trunk_w = rng.randint(3, 5)
            trunk_x = cx - trunk_w // 2
            trunk_y = cy + 6
            pygame.draw.rect(surface, (55, 35, 15),
                             (trunk_x - 1, trunk_y - trunk_h - 1,
                              trunk_w + 2, trunk_h + 2))
            pygame.draw.rect(surface, (100, 70, 35),
                             (trunk_x, trunk_y - trunk_h,
                              trunk_w, trunk_h))
            pygame.draw.line(surface, (80, 50, 25),
                             (trunk_x + trunk_w // 2,
                              trunk_y - trunk_h),
                             (trunk_x + trunk_w // 2, trunk_y), 1)
            foliage_layers = rng.randint(2, 4)
            for i in range(foliage_layers):
                fy = trunk_y - trunk_h - i * 7
                fw = rng.randint(14, 22) - i * 3
                g_val = rng.randint(50, 90)
                leaf_c = (30 + rng.randint(0, 20), g_val + 65, 20)
                leaf_dk = (15, g_val + 35, 10)
                pts = [(cx - fw // 2, fy + 7), (cx, fy - 7),
                       (cx + fw // 2, fy + 7)]
                pygame.draw.polygon(surface, leaf_dk, pts)
                inner = [(cx - fw // 2 + 1, fy + 6), (cx, fy - 5),
                         (cx + fw // 2 - 1, fy + 6)]
                pygame.draw.polygon(surface, leaf_c, inner)
        elif deco_type <= 7:
            for _ in range(rng.randint(2, 4)):
                rx = cx + rng.randint(-ts // 4, ts // 4)
                ry = cy + rng.randint(-ts // 4, ts // 4)
                rock_r = rng.randint(4, 9)
                rc = rng.randint(100, 140)
                pygame.draw.circle(surface, (rc - 30, rc - 35, rc - 45),
                                   (rx, ry), rock_r + 1)
                pygame.draw.circle(surface, (rc + 5, rc, rc - 10),
                                   (rx, ry), rock_r)
                hl_c = (min(255, rc + 15), min(255, rc + 10), max(0, rc))
                pygame.draw.ellipse(surface, hl_c,
                                    (rx - rock_r, ry - rock_r,
                                     rock_r * 2, rock_r))
        elif deco_type <= 9:
            for _ in range(rng.randint(2, 5)):
                bx = cx + rng.randint(-ts // 3, ts // 3)
                by = cy + rng.randint(-ts // 4, ts // 4)
                bw = rng.randint(9, 16)
                bh = rng.randint(7, 12)
                g_val = rng.randint(90, 150)
                bush_c = (40 + rng.randint(0, 15), g_val, 30)
                bush_dk = (25, g_val - 25, 18)
                pygame.draw.ellipse(surface, bush_dk,
                                    (bx - bw // 2 - 1, by - bh // 2 - 1,
                                     bw + 2, bh + 2))
                pygame.draw.ellipse(surface, bush_c,
                                    (bx - bw // 2, by - bh // 2, bw, bh))
                if rng.random() < 0.4:
                    fx = bx + rng.randint(-2, 2)
                    fy = by - bh // 2 + rng.randint(0, 3)
                    fc = rng.choice([(255, 210, 80), (255, 170, 120),
                                     (255, 200, 200)])
                    pygame.draw.circle(surface, fc, (fx, fy), 2)

    def _draw_spawn_portal(self, game_map):
        """Draw a fiery demon portal at the enemy spawn point."""
        waypoints = game_map.get_path_pixel_waypoints()
        if not waypoints:
            return
        sx, sy = waypoints[0]
        t = self.anim_tick * 0.06

        for i in range(4):
            r = 20 + i * 7 + int(math.sin(t + i * 0.8) * 3)
            alpha = max(0, 100 - i * 22)
            color = (120 + i * 25, 20 + i * 10, 160 + i * 15)
            surf = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
            pygame.draw.circle(surf, (*color, alpha), (r, r), r, 3)
            self.screen.blit(surf, (sx - r, sy - r))

        inner_r = 12 + int(math.sin(t * 2) * 3)
        core_surf = pygame.Surface((inner_r * 2 + 4, inner_r * 2 + 4),
                                   pygame.SRCALPHA)
        cr = inner_r + 2
        pygame.draw.circle(core_surf, (80, 10, 100, 200), (cr, cr), inner_r)
        pygame.draw.circle(core_surf, (50, 0, 70, 255), (cr, cr),
                           inner_r - 3)
        pygame.draw.circle(core_surf, (160, 60, 220, 180), (cr, cr),
                           inner_r, 2)
        self.screen.blit(core_surf, (sx - cr, sy - cr))

        swirl_count = 6
        for i in range(swirl_count):
            a = t * 3 + (math.pi * 2 / swirl_count) * i
            sr = 15 + int(math.sin(t + i * 1.5) * 3)
            px = int(sx + math.cos(a) * sr)
            py = int(sy + math.sin(a) * sr)
            pc = (220, 140 + int(math.sin(t * 2 + i) * 40), 255)
            pygame.draw.circle(self.screen, pc, (px, py), 2)

        for i in range(3):
            fa = t * 2 + i * 2.1
            fr = 6 + int(math.sin(fa) * 4)
            fpx = int(sx + math.cos(fa * 1.3) * fr)
            fpy = int(sy + math.sin(fa * 1.3) * fr)
            pygame.draw.circle(self.screen, (255, 200, 255), (fpx, fpy), 1)

    def _draw_base_castle(self, game_map, base_hp, base_max_hp,
                          base_level=1, selected_base=False):
        """Draw a large, detailed castle at the base (end of path)."""
        waypoints = game_map.get_path_pixel_waypoints()
        if not waypoints:
            return
        bx, by = waypoints[-1]
        ts = self.tile_size
        pulse = int(abs(math.sin(self.anim_tick * 0.04)) * 3)

        if selected_base:
            sel_r = ts - 4
            sel_surf = pygame.Surface((sel_r * 2, sel_r * 2), pygame.SRCALPHA)
            ring_alpha = 100 + int(abs(math.sin(self.anim_tick * 0.08)) * 100)
            pygame.draw.circle(sel_surf, (255, 220, 80, ring_alpha),
                               (sel_r, sel_r), sel_r, 3)
            self.screen.blit(sel_surf, (bx - sel_r, by - sel_r))

        wall_w = ts + 16
        wall_h = ts + 8
        wx = bx - wall_w // 2
        wy = by - wall_h // 2

        shadow_surf = pygame.Surface((wall_w + 10, wall_h + 10), pygame.SRCALPHA)
        pygame.draw.rect(shadow_surf, (0, 0, 0, 70),
                         (5, 5, wall_w, wall_h), border_radius=4)
        self.screen.blit(shadow_surf, (wx, wy))

        stone_base = (130, 105, 70)
        stone_light = (160, 135, 95)
        stone_dark = (100, 80, 55)
        pygame.draw.rect(self.screen, stone_base,
                         (wx, wy, wall_w, wall_h), border_radius=3)
        pygame.draw.rect(self.screen, stone_light,
                         (wx + 3, wy + 3, wall_w - 6, wall_h - 6),
                         border_radius=3)

        for row_i in range(4):
            for col_i in range(5):
                brx = wx + 4 + col_i * (wall_w - 8) // 5
                bry = wy + 4 + row_i * (wall_h - 8) // 4
                brw = (wall_w - 16) // 5
                brh = (wall_h - 16) // 4
                offset = (row_i % 2) * (brw // 2)
                pygame.draw.rect(self.screen, stone_dark,
                                 (brx + offset, bry, brw, brh), 1)

        turret_w = 14
        turret_h = 22 + pulse
        turret_positions = [
            (wx - 2, wy),
            (wx + wall_w - turret_w + 2, wy),
        ]
        for tx, _ in turret_positions:
            ty = wy - turret_h + 6
            pygame.draw.rect(self.screen, (150, 118, 78),
                             (tx, ty, turret_w, turret_h + 2))
            pygame.draw.rect(self.screen, stone_dark,
                             (tx, ty, turret_w, turret_h + 2), 1)
            for ci in range(4):
                cw = 3
                cx_pos = tx + 1 + ci * 3
                pygame.draw.rect(self.screen, (90, 68, 44),
                                 (cx_pos, ty, cw, 5))
            cap_y = ty - 8
            pygame.draw.polygon(self.screen, (180, 50, 40), [
                (tx + turret_w // 2, cap_y),
                (tx - 1, ty + 1),
                (tx + turret_w + 1, ty + 1),
            ])
            pygame.draw.polygon(self.screen, (140, 30, 25), [
                (tx + turret_w // 2, cap_y),
                (tx - 1, ty + 1),
                (tx + turret_w + 1, ty + 1),
            ], 1)

        keep_w = 20
        keep_h = 28 + pulse
        kx = bx - keep_w // 2
        ky = wy - keep_h + 8
        pygame.draw.rect(self.screen, (145, 115, 80),
                         (kx, ky, keep_w, keep_h))
        pygame.draw.rect(self.screen, stone_dark,
                         (kx, ky, keep_w, keep_h), 1)
        for ci in range(5):
            cw = 3
            cx_pos = kx + 1 + ci * 4
            pygame.draw.rect(self.screen, (90, 68, 44),
                             (cx_pos, ky, cw, 5))

        window_y = ky + 10
        for wx_off in [-4, 4]:
            pygame.draw.rect(self.screen, (30, 20, 10),
                             (bx + wx_off - 2, window_y, 4, 6))
            pygame.draw.rect(self.screen, (70, 50, 30),
                             (bx + wx_off - 2, window_y, 4, 6), 1)

        gate_w, gate_h = 18, 22
        gate_x = bx - gate_w // 2
        gate_y = by + wall_h // 2 - gate_h
        pygame.draw.rect(self.screen, (45, 28, 12),
                         (gate_x, gate_y, gate_w, gate_h),
                         border_radius=8)
        pygame.draw.rect(self.screen, (75, 52, 28),
                         (gate_x, gate_y, gate_w, gate_h), 2,
                         border_radius=8)
        for bar_off in range(3, gate_w - 2, 4):
            pygame.draw.line(self.screen, (65, 45, 22),
                             (gate_x + bar_off, gate_y + 5),
                             (gate_x + bar_off, gate_y + gate_h - 2), 1)
        pygame.draw.circle(self.screen, (200, 170, 80),
                           (gate_x + gate_w - 4, gate_y + gate_h // 2), 2)

        for fi, (fx, fy) in enumerate([(bx - 4, ky - 10), (bx + 10, ky - 6)]):
            pole_h = 16
            pygame.draw.line(self.screen, (180, 180, 180),
                             (fx, fy), (fx, fy + pole_h), 2)
            wave_off = int(math.sin(self.anim_tick * 0.12 + fi * 1.5) * 3)
            flag_c = (200, 40, 40) if fi == 0 else (40, 80, 200)
            pygame.draw.polygon(self.screen, flag_c, [
                (fx + 1, fy),
                (fx + 12 + wave_off, fy + 4),
                (fx + 1, fy + 8)
            ])

        ratio = base_hp / base_max_hp if base_max_hp > 0 else 0
        bar_total_w = wall_w + 12
        bar_h = 7
        bar_x = bx - bar_total_w // 2
        bar_y_pos = ky - 16
        pygame.draw.rect(self.screen, (40, 10, 10),
                         (bar_x - 1, bar_y_pos - 1,
                          bar_total_w + 2, bar_h + 2),
                         border_radius=3)
        if ratio > 0.6:
            bar_c = (30, 200, 50)
        elif ratio > 0.3:
            bar_c = (220, 180, 30)
        else:
            bar_c = (220, 40, 30)
        fg_w = int(bar_total_w * ratio)
        if fg_w > 0:
            pygame.draw.rect(self.screen, bar_c,
                             (bar_x, bar_y_pos, fg_w, bar_h),
                             border_radius=3)
        if fg_w > 4:
            shine = pygame.Surface((fg_w - 4, bar_h // 3), pygame.SRCALPHA)
            shine.fill((255, 255, 255, 50))
            self.screen.blit(shine, (bar_x + 2, bar_y_pos + 1))
        pygame.draw.rect(self.screen, (200, 200, 200),
                         (bar_x - 1, bar_y_pos - 1,
                          bar_total_w + 2, bar_h + 2), 1,
                         border_radius=3)

        lvl_text = self.font_tiny.render(
            f"Lv{base_level}", True, (255, 220, 100))
        self.screen.blit(lvl_text,
                         (bx - lvl_text.get_width() // 2, bar_y_pos - 14))

    # ------------------------------------------------------------------
    # Build spots
    # ------------------------------------------------------------------

    def _draw_build_spots(self, game_map, colors, hover_pos,
                          selected_tower_type):
        """Draw valid build spots with animated markers."""
        ts = self.tile_size
        for col, row in game_map.build_spots:
            cx = col * ts + ts // 2
            cy = row * ts + ts // 2
            is_hover = (selected_tower_type is not None
                        and hover_pos is not None
                        and hover_pos == (col, row))
            if is_hover:
                rect = pygame.Rect(col * ts + 2, row * ts + 2,
                                   ts - 4, ts - 4)
                surf = pygame.Surface((ts - 4, ts - 4), pygame.SRCALPHA)
                surf.fill((120, 255, 120, 50))
                self.screen.blit(surf, rect)
                pygame.draw.rect(self.screen, (180, 255, 180), rect, 2,
                                 border_radius=4)
                cross_surf = pygame.Surface((ts - 4, ts - 4), pygame.SRCALPHA)
                cross_s = 6
                csx = (ts - 4) // 2
                csy = (ts - 4) // 2
                pygame.draw.line(cross_surf, (255, 255, 255, 160),
                                 (csx - cross_s, csy),
                                 (csx + cross_s, csy), 1)
                pygame.draw.line(cross_surf, (255, 255, 255, 160),
                                 (csx, csy - cross_s),
                                 (csx, csy + cross_s), 1)
                self.screen.blit(cross_surf, rect)
            else:
                pulse = abs(math.sin(self.anim_tick * 0.04 + col + row))
                alpha = int(50 + pulse * 60)
                r = int(9 + pulse * 3)
                surf = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
                pygame.draw.circle(surf, (130, 220, 100, alpha),
                                   (r, r), r, 2)
                self.screen.blit(surf, (cx - r, cy - r))

    # ------------------------------------------------------------------
    # Shadows helper
    # ------------------------------------------------------------------

    def _draw_shadow(self, cx, cy, radius):
        """Draw an elliptical shadow beneath an entity."""
        surf = pygame.Surface((radius * 2, radius), pygame.SRCALPHA)
        pygame.draw.ellipse(surf, (0, 0, 0, 50),
                            (0, 0, radius * 2, radius))
        self.screen.blit(surf, (cx - radius, cy - radius // 2))

    def _draw_tower_shadow(self, tower):
        """Draw a shadow under a tower."""
        cx, cy = tower.pixel_x, tower.pixel_y
        r = self.tile_size // 3 + 4
        surf = pygame.Surface((r * 2, r), pygame.SRCALPHA)
        pygame.draw.ellipse(surf, (0, 0, 0, 40), (0, 0, r * 2, r))
        self.screen.blit(surf, (cx - r, cy + r // 2))

    # ------------------------------------------------------------------
    # Towers
    # ------------------------------------------------------------------

    def _draw_towers(self, towers, colors):
        """Draw all towers."""
        draw_map = {
            TowerType.ARCHER: self._draw_archer_tower,
            TowerType.BARRACKS: self._draw_barracks_tower,
            TowerType.MAGE: self._draw_mage_tower,
            TowerType.ARTILLERY: self._draw_artillery_tower,
            TowerType.FREEZE: self._draw_freeze_tower,
            TowerType.POISON: self._draw_poison_tower,
            TowerType.BALLISTA: self._draw_ballista_tower,
            TowerType.TESLA: self._draw_tesla_tower,
            TowerType.NECROMANCER: self._draw_necromancer_tower,
            TowerType.LASER: self._draw_laser_tower,
        }
        for tower in towers:
            cx, cy = tower.pixel_x, tower.pixel_y
            ts = self.tile_size
            draw_fn = draw_map.get(tower.tower_type)
            if draw_fn is not None:
                draw_fn(cx, cy, ts, tower)
            if hasattr(tower, 'tower_hp') and tower.tower_hp < tower.tower_max_hp:
                bar_w = ts // 2
                bar_h = 3
                bar_x = cx - bar_w // 2
                bar_y = cy + ts // 4 + 20
                self._draw_health_bar(
                    bar_x, bar_y, bar_w, bar_h,
                    tower.get_tower_hp_ratio(), self.config["colors"])

    def _draw_tower_platform(self, cx, cy, ts, color):
        """Draw a warm stone tower base platform with depth."""
        pw, ph = ts // 2 + 10, 12
        px = cx - pw // 2
        py = cy + ts // 4 - 5
        outline = tuple(max(0, c - 50) for c in color)
        pygame.draw.rect(self.screen, outline,
                         (px - 1, py, pw + 2, ph + 2),
                         border_radius=4)
        pygame.draw.rect(self.screen, color,
                         (px, py + 1, pw, ph), border_radius=3)
        lighter = tuple(min(255, c + 35) for c in color)
        hl_surf = pygame.Surface((pw - 4, ph // 2), pygame.SRCALPHA)
        pygame.draw.rect(hl_surf, (*lighter, 70),
                         hl_surf.get_rect(), border_radius=2)
        self.screen.blit(hl_surf, (px + 2, py + 2))

    def _draw_archer_tower(self, cx, cy, ts, tower):
        """Draw a detailed wooden archer tower with bowman and bold outlines."""
        outline = (50, 35, 20)
        self._draw_tower_platform(cx, cy, ts, (120, 95, 65))
        base_w = ts // 2 + 2
        base_h = ts // 2 + 6
        bx = cx - base_w // 2
        by = cy - base_h // 2 - 2

        pygame.draw.rect(self.screen, outline,
                         (bx - 1, by - 1, base_w + 2, base_h + 2),
                         border_radius=3)
        pygame.draw.rect(self.screen, (140, 110, 75),
                         (bx, by, base_w, base_h), border_radius=2)
        hl_surf = pygame.Surface((base_w - 4, base_h // 3), pygame.SRCALPHA)
        pygame.draw.rect(hl_surf, (180, 155, 115, 60),
                         hl_surf.get_rect(), border_radius=2)
        self.screen.blit(hl_surf, (bx + 2, by + 2))

        plank_gap = base_h // 4
        for i in range(1, 4):
            py_line = by + i * plank_gap
            pygame.draw.line(self.screen, (110, 82, 52),
                             (bx + 2, py_line), (bx + base_w - 2, py_line), 1)

        window_w, window_h = 5, 4
        pygame.draw.rect(self.screen, outline,
                         (cx - window_w // 2, by + base_h // 2 - 1,
                          window_w, window_h), border_radius=1)
        pygame.draw.rect(self.screen, (60, 45, 25),
                         (cx - window_w // 2 + 1, by + base_h // 2,
                          window_w - 2, window_h - 2))

        top_y = by - 8
        roof_pts = [
            (cx - base_w // 2 - 5, by + 2),
            (cx, top_y),
            (cx + base_w // 2 + 5, by + 2)
        ]
        pygame.draw.polygon(self.screen, outline, roof_pts)
        inner_roof = [
            (cx - base_w // 2 - 3, by + 1),
            (cx, top_y + 2),
            (cx + base_w // 2 + 3, by + 1)
        ]
        pygame.draw.polygon(self.screen, (20, 160, 45), inner_roof)
        pygame.draw.line(self.screen, (15, 120, 30),
                         inner_roof[0], inner_roof[2], 1)

        head_y = by + 8
        pygame.draw.circle(self.screen, outline, (cx, head_y), 6)
        pygame.draw.circle(self.screen, (225, 190, 155), (cx, head_y), 5)
        pygame.draw.circle(self.screen, (200, 165, 130),
                           (cx + 1, head_y + 1), 3)
        for ex in [-2, 2]:
            pygame.draw.circle(self.screen, (255, 255, 240),
                               (cx + ex, head_y - 1), 2)
            pygame.draw.circle(self.screen, (30, 20, 10),
                               (cx + ex, head_y - 1), 1)

        if tower.target and tower.target.is_alive:
            dx = tower.target.x - cx
            dy = tower.target.y - cy
            dist = math.sqrt(dx * dx + dy * dy)
            if dist > 0:
                ndx, ndy = dx / dist, dy / dist
                bow_len = 15
                bex = int(cx + ndx * bow_len)
                bey = int(head_y + ndy * bow_len)
                pygame.draw.line(self.screen, outline,
                                 (cx, head_y), (bex, bey), 3)
                pygame.draw.line(self.screen, (120, 75, 30),
                                 (cx, head_y), (bex, bey), 2)
                pygame.draw.circle(self.screen, (200, 140, 50),
                                   (bex, bey), 3)
                pygame.draw.circle(self.screen, outline, (bex, bey), 3, 1)

        self._draw_tower_level_stars(cx, cy + ts // 4 + 8, tower.level)

    def _draw_mage_tower(self, cx, cy, ts, tower):
        """Draw a detailed crystal mage tower with arcane effects."""
        outline = (40, 20, 55)
        self._draw_tower_platform(cx, cy, ts, (90, 55, 110))
        base_w = ts // 2
        base_h = ts // 2 + 10
        bx = cx - base_w // 2
        by = cy - base_h // 2 - 4

        tower_pts = [
            (cx - base_w // 2 - 1, by + base_h + 1),
            (cx - base_w // 3, by - 1),
            (cx + base_w // 3, by - 1),
            (cx + base_w // 2 + 1, by + base_h + 1)
        ]
        pygame.draw.polygon(self.screen, outline, tower_pts)
        inner_pts = [
            (cx - base_w // 2, by + base_h),
            (cx - base_w // 3 + 1, by),
            (cx + base_w // 3 - 1, by),
            (cx + base_w // 2, by + base_h)
        ]
        pygame.draw.polygon(self.screen, (100, 50, 145), inner_pts)

        hl_surf = pygame.Surface((base_w // 3, base_h - 6), pygame.SRCALPHA)
        pygame.draw.rect(hl_surf, (140, 90, 190, 50),
                         hl_surf.get_rect(), border_radius=2)
        self.screen.blit(hl_surf, (cx - base_w // 6, by + 3))

        for i in range(3):
            wy = by + 7 + i * (base_h // 3)
            ww = max(3, base_w // 4 - i * 2)
            pygame.draw.rect(self.screen, outline,
                             (cx - ww // 2 - 1, wy - 1, ww + 2, ww + 2),
                             border_radius=1)
            glow_val = 180 + int(math.sin(self.anim_tick * 0.1 + i) * 50)
            inner_c = (min(255, glow_val), 100, 255)
            pygame.draw.rect(self.screen, inner_c,
                             (cx - ww // 2, wy, ww, ww))
            pygame.draw.rect(self.screen, (255, 220, 255, 100),
                             (cx - ww // 2, wy, ww, 1))

        spire_h = 12
        spire_pts = [(cx - 5, by), (cx, by - spire_h), (cx + 5, by)]
        pygame.draw.polygon(self.screen, outline, spire_pts)
        pygame.draw.polygon(self.screen, (130, 65, 180),
                            [(cx - 4, by), (cx, by - spire_h + 1),
                             (cx + 4, by)])

        orb_r = 7 + int(abs(math.sin(self.anim_tick * 0.08)) * 3)
        orb_y = by - spire_h
        glow_surf = pygame.Surface((orb_r * 4, orb_r * 4), pygame.SRCALPHA)
        pygame.draw.circle(glow_surf, (160, 80, 255, 40),
                           (orb_r * 2, orb_r * 2), orb_r * 2)
        pygame.draw.circle(glow_surf, (190, 120, 255, 80),
                           (orb_r * 2, orb_r * 2), orb_r)
        pygame.draw.circle(glow_surf, (230, 200, 255, 160),
                           (orb_r * 2, orb_r * 2), orb_r // 2)
        pygame.draw.circle(glow_surf, (255, 240, 255, 220),
                           (orb_r * 2 - 1, orb_r * 2 - 1), max(1, orb_r // 3))
        self.screen.blit(glow_surf, (cx - orb_r * 2, orb_y - orb_r))

        sparkle_count = 4
        for i in range(sparkle_count):
            a = self.anim_tick * 0.05 + (math.pi * 2 / sparkle_count) * i
            sr = orb_r + 7
            spx = int(cx + math.cos(a) * sr)
            spy = int(orb_y + math.sin(a) * sr)
            pygame.draw.circle(self.screen, (230, 200, 255), (spx, spy), 2)
            pygame.draw.circle(self.screen, (255, 240, 255), (spx, spy), 1)

        self._draw_tower_level_stars(cx, cy + ts // 4 + 8, tower.level)

    def _draw_artillery_tower(self, cx, cy, ts, tower):
        """Draw a cannon/artillery tower."""
        self._draw_tower_platform(cx, cy, ts, (90, 90, 90))
        base_w = ts // 2 + 4
        base_h = ts // 3 + 4
        bx = cx - base_w // 2
        by = cy - base_h // 2

        pygame.draw.rect(self.screen, (110, 110, 115),
                         (bx, by, base_w, base_h), border_radius=3)
        pygame.draw.rect(self.screen, (80, 80, 85),
                         (bx, by, base_w, base_h), 2, border_radius=3)
        rivet_positions = [
            (bx + 4, by + 4), (bx + base_w - 5, by + 4),
            (bx + 4, by + base_h - 5), (bx + base_w - 5, by + base_h - 5)
        ]
        for rx, ry in rivet_positions:
            pygame.draw.circle(self.screen, (140, 140, 145), (rx, ry), 2)

        barrel_len = ts // 3 + 6
        angle = 0.0
        if tower.target and tower.target.is_alive:
            dx = tower.target.x - cx
            dy = tower.target.y - cy
            angle = math.atan2(dy, dx)
        cos_a, sin_a = math.cos(angle), math.sin(angle)
        ex = int(cx + barrel_len * cos_a)
        ey = int(cy + barrel_len * sin_a)

        perp_x, perp_y = -sin_a * 4, cos_a * 4
        barrel_pts = [
            (int(cx + perp_x), int(cy + perp_y)),
            (int(cx - perp_x), int(cy - perp_y)),
            (int(ex - perp_x * 0.6), int(ey - perp_y * 0.6)),
            (int(ex + perp_x * 0.6), int(ey + perp_y * 0.6)),
        ]
        pygame.draw.polygon(self.screen, (65, 65, 70), barrel_pts)
        pygame.draw.polygon(self.screen, (45, 45, 50), barrel_pts, 2)

        pygame.draw.circle(self.screen, (200, 130, 20), (cx, cy), 7)
        pygame.draw.circle(self.screen, (160, 100, 10), (cx, cy), 7, 2)

        muzzle_x = int(ex + cos_a * 2)
        muzzle_y = int(ey + sin_a * 2)
        pygame.draw.circle(self.screen, (50, 50, 55), (muzzle_x, muzzle_y), 3)

        self._draw_tower_level_stars(cx, cy + ts // 4 + 8, tower.level)

    def _draw_barracks_tower(self, cx, cy, ts, tower):
        """Draw a barracks tower with tent/banner style."""
        self._draw_tower_platform(cx, cy, ts, (70, 60, 100))
        base_w = ts // 2 + 4
        base_h = ts // 2 + 4
        bx = cx - base_w // 2
        by = cy - base_h // 2 - 2

        pygame.draw.rect(self.screen, (65, 85, 145),
                         (bx, by, base_w, base_h), border_radius=4)
        pygame.draw.rect(self.screen, (85, 105, 165),
                         (bx + 2, by + 2, base_w - 4, base_h - 4),
                         border_radius=3)
        pygame.draw.rect(self.screen, (50, 65, 120),
                         (bx, by, base_w, base_h), 2, border_radius=4)

        shield_cx = cx
        shield_cy = cy - 2
        shield_r = 8
        pygame.draw.circle(self.screen, (180, 180, 50),
                           (shield_cx, shield_cy), shield_r)
        pygame.draw.circle(self.screen, (140, 140, 30),
                           (shield_cx, shield_cy), shield_r, 2)
        pygame.draw.line(self.screen, (140, 140, 30),
                         (shield_cx, shield_cy - 5),
                         (shield_cx, shield_cy + 5), 2)
        pygame.draw.line(self.screen, (140, 140, 30),
                         (shield_cx - 5, shield_cy),
                         (shield_cx + 5, shield_cy), 2)

        flag_x = cx + base_w // 2 - 4
        flag_y = by - 2
        pygame.draw.line(self.screen, (200, 200, 200),
                         (flag_x, flag_y), (flag_x, flag_y + base_h + 2), 2)
        wave_off = int(math.sin(self.anim_tick * 0.1) * 3)
        pygame.draw.polygon(self.screen, (200, 50, 50), [
            (flag_x + 1, flag_y - 2),
            (flag_x + 12 + wave_off, flag_y + 3),
            (flag_x + 1, flag_y + 8)
        ])

        self._draw_tower_level_stars(cx, cy + ts // 4 + 8, tower.level)

    def _draw_freeze_tower(self, cx, cy, ts, tower):
        """Draw a freeze/ice tower."""
        self._draw_tower_platform(cx, cy, ts, (80, 120, 160))
        base_w = ts // 2
        base_h = ts // 2 + 6
        bx = cx - base_w // 2
        by = cy - base_h // 2 - 2

        pygame.draw.polygon(self.screen, (140, 200, 240), [
            (cx - base_w // 2, by + base_h),
            (cx - base_w // 3, by),
            (cx + base_w // 3, by),
            (cx + base_w // 2, by + base_h)
        ])
        pygame.draw.polygon(self.screen, (100, 170, 220), [
            (cx - base_w // 2, by + base_h),
            (cx - base_w // 3, by),
            (cx + base_w // 3, by),
            (cx + base_w // 2, by + base_h)
        ], 2)

        crystal_y = by - 4
        glow = int(abs(math.sin(self.anim_tick * 0.1)) * 4)
        pygame.draw.polygon(self.screen, (180, 230, 255), [
            (cx, crystal_y - 10 - glow),
            (cx - 6, crystal_y),
            (cx + 6, crystal_y)
        ])
        pygame.draw.polygon(self.screen, (220, 245, 255), [
            (cx, crystal_y - 10 - glow),
            (cx - 6, crystal_y),
            (cx + 6, crystal_y)
        ], 1)

        for i in range(3):
            a = self.anim_tick * 0.04 + i * 2.1
            sr = 14 + glow
            spx = int(cx + math.cos(a) * sr)
            spy = int(cy + math.sin(a) * sr)
            pygame.draw.circle(self.screen, (200, 240, 255), (spx, spy), 2)

        self._draw_tower_level_stars(cx, cy + ts // 4 + 8, tower.level)

    def _draw_poison_tower(self, cx, cy, ts, tower):
        """Draw a poison/toxic tower."""
        self._draw_tower_platform(cx, cy, ts, (60, 90, 40))
        base_r = ts // 3
        pygame.draw.circle(self.screen, (50, 100, 30), (cx, cy), base_r)
        pygame.draw.circle(self.screen, (70, 130, 40), (cx, cy), base_r, 2)

        bubble_t = self.anim_tick * 0.08
        for i in range(4):
            a = bubble_t + i * 1.57
            br = 3 + int(abs(math.sin(a)) * 3)
            bpx = int(cx + math.cos(a) * (base_r - 6))
            bpy = int(cy + math.sin(a) * (base_r - 6))
            pygame.draw.circle(self.screen, (120, 220, 60), (bpx, bpy), br)
            pygame.draw.circle(self.screen, (80, 180, 30), (bpx, bpy), br, 1)

        skull_y = cy - 3
        pygame.draw.circle(self.screen, (200, 255, 100), (cx, skull_y), 6)
        pygame.draw.circle(self.screen, (40, 60, 20), (cx - 2, skull_y - 1), 2)
        pygame.draw.circle(self.screen, (40, 60, 20), (cx + 2, skull_y - 1), 2)

        self._draw_tower_level_stars(cx, cy + ts // 4 + 8, tower.level)

    def _draw_laser_tower(self, cx, cy, ts, tower):
        """Draw a high-tech laser tower."""
        self._draw_tower_platform(cx, cy, ts, (100, 60, 60))
        base_w = ts // 2 - 2
        base_h = ts // 2 + 8
        bx = cx - base_w // 2
        by = cy - base_h // 2 - 4

        pygame.draw.rect(self.screen, (80, 40, 50),
                         (bx, by, base_w, base_h), border_radius=3)
        pygame.draw.rect(self.screen, (120, 60, 70),
                         (bx, by, base_w, base_h), 2, border_radius=3)

        lens_y = by - 2
        glow = int(abs(math.sin(self.anim_tick * 0.12)) * 5)
        pygame.draw.circle(self.screen, (255, 50, 50), (cx, lens_y), 7 + glow)
        pygame.draw.circle(self.screen, (255, 150, 150), (cx, lens_y), 4)
        pygame.draw.circle(self.screen, (255, 255, 200), (cx, lens_y), 2)

        if tower.target and tower.target.is_alive:
            tx, ty = int(tower.target.x), int(tower.target.y)
            beam_surf = pygame.Surface(
                (self.config["screen"]["width"],
                 self.config["screen"]["height"]), pygame.SRCALPHA)
            pygame.draw.line(beam_surf, (255, 40, 40, 40),
                             (cx, lens_y), (tx, ty), 12)
            pygame.draw.line(beam_surf, (255, 80, 80, 100),
                             (cx, lens_y), (tx, ty), 6)
            pygame.draw.line(beam_surf, (255, 200, 200, 180),
                             (cx, lens_y), (tx, ty), 3)
            pygame.draw.line(beam_surf, (255, 255, 240, 220),
                             (cx, lens_y), (tx, ty), 1)
            self.screen.blit(beam_surf, (0, 0))
            pygame.draw.circle(self.screen, (255, 100, 100), (tx, ty), 6)
            pygame.draw.circle(self.screen, (255, 220, 180), (tx, ty), 3)

        self._draw_tower_level_stars(cx, cy + ts // 4 + 8, tower.level)

    def _draw_ballista_tower(self, cx, cy, ts, tower):
        """Draw a heavy ballista/crossbow tower."""
        self._draw_tower_platform(cx, cy, ts, (100, 80, 50))
        base_w = ts // 2 + 4
        base_h = ts // 3
        bx = cx - base_w // 2
        by = cy - base_h // 2
        pygame.draw.rect(self.screen, (110, 85, 55),
                         (bx, by, base_w, base_h), border_radius=3)
        pygame.draw.rect(self.screen, (80, 60, 35),
                         (bx, by, base_w, base_h), 2, border_radius=3)

        bolt_len = ts // 3 + 10
        angle = 0.0
        if tower.target and tower.target.is_alive:
            dx = tower.target.x - cx
            dy_val = tower.target.y - cy
            angle = math.atan2(dy_val, dx)
        cos_a, sin_a = math.cos(angle), math.sin(angle)
        ex = int(cx + bolt_len * cos_a)
        ey = int(cy + bolt_len * sin_a)

        arm_w = 18
        left_arm = (int(cx - sin_a * arm_w), int(cy + cos_a * arm_w))
        right_arm = (int(cx + sin_a * arm_w), int(cy - cos_a * arm_w))
        pygame.draw.line(self.screen, (90, 70, 40),
                         left_arm, right_arm, 4)
        pygame.draw.line(self.screen, (60, 45, 25),
                         (cx, cy), (ex, ey), 3)
        pygame.draw.circle(self.screen, (180, 140, 60),
                           (int(ex), int(ey)), 3)

        pygame.draw.circle(self.screen, (140, 110, 60), (cx, cy), 5)
        pygame.draw.circle(self.screen, (100, 75, 40), (cx, cy), 5, 2)
        self._draw_tower_level_stars(cx, cy + ts // 4 + 8, tower.level)

    def _draw_tesla_tower(self, cx, cy, ts, tower):
        """Draw an electric tesla coil tower."""
        self._draw_tower_platform(cx, cy, ts, (70, 70, 100))
        base_w = ts // 2 - 4
        base_h = ts // 2 + 10
        bx = cx - base_w // 2
        by = cy - base_h // 2 - 4

        pygame.draw.rect(self.screen, (80, 80, 110),
                         (bx, by, base_w, base_h), border_radius=3)
        pygame.draw.rect(self.screen, (50, 50, 80),
                         (bx, by, base_w, base_h), 2, border_radius=3)

        for ri in range(3):
            ry_pos = by + 4 + ri * (base_h // 3)
            ring_w = base_w - 4 + ri * 2
            pygame.draw.ellipse(self.screen, (100, 100, 140),
                                (cx - ring_w // 2, ry_pos, ring_w, 6), 2)

        coil_y = by - 6
        glow = int(abs(math.sin(self.anim_tick * 0.15)) * 6)
        orb_r = 7 + glow
        glow_surf = pygame.Surface((orb_r * 4, orb_r * 4), pygame.SRCALPHA)
        pygame.draw.circle(glow_surf, (80, 140, 255, 60),
                           (orb_r * 2, orb_r * 2), orb_r * 2)
        pygame.draw.circle(glow_surf, (120, 180, 255, 120),
                           (orb_r * 2, orb_r * 2), orb_r)
        self.screen.blit(glow_surf, (cx - orb_r * 2, coil_y - orb_r))
        pygame.draw.circle(self.screen, (180, 220, 255), (cx, coil_y), 5)

        for i in range(4):
            a = self.anim_tick * 0.08 + i * 1.57
            sr = 12 + glow
            spx = int(cx + math.cos(a) * sr)
            spy = int(coil_y + math.sin(a) * sr)
            pygame.draw.line(self.screen, (100, 160, 255),
                             (cx, coil_y), (spx, spy), 1)

        if tower.target and tower.target.is_alive:
            tx, ty = int(tower.target.x), int(tower.target.y)
            seg = 6
            prev = (cx, coil_y)
            bolt_surf = pygame.Surface(
                (self.config["screen"]["width"],
                 self.config["screen"]["height"]), pygame.SRCALPHA)
            for si in range(seg):
                t_frac = (si + 1) / seg
                ix = int(cx + (tx - cx) * t_frac)
                iy = int(coil_y + (ty - coil_y) * t_frac)
                if si < seg - 1:
                    ix += random.randint(-8, 8)
                    iy += random.randint(-8, 8)
                pygame.draw.line(bolt_surf, (60, 120, 255, 50),
                                 prev, (ix, iy), 8)
                pygame.draw.line(bolt_surf, (120, 200, 255, 150),
                                 prev, (ix, iy), 4)
                pygame.draw.line(self.screen, (200, 240, 255),
                                 prev, (ix, iy), 2)
                prev = (ix, iy)
            self.screen.blit(bolt_surf, (0, 0))
            pygame.draw.circle(self.screen, (150, 220, 255), (tx, ty), 5)
            pygame.draw.circle(self.screen, (230, 245, 255), (tx, ty), 3)

        self._draw_tower_level_stars(cx, cy + ts // 4 + 8, tower.level)

    def _draw_necromancer_tower(self, cx, cy, ts, tower):
        """Draw a dark necromancer tower with skull motif."""
        self._draw_tower_platform(cx, cy, ts, (60, 40, 70))
        base_w = ts // 2
        base_h = ts // 2 + 8
        bx = cx - base_w // 2
        by = cy - base_h // 2 - 4

        tower_pts = [
            (cx - base_w // 2, by + base_h),
            (cx - base_w // 3, by),
            (cx + base_w // 3, by),
            (cx + base_w // 2, by + base_h)
        ]
        pygame.draw.polygon(self.screen, (50, 25, 60), tower_pts)
        pygame.draw.polygon(self.screen, (80, 40, 90), tower_pts, 2)

        skull_y = by + base_h // 3
        pygame.draw.circle(self.screen, (200, 200, 180), (cx, skull_y), 7)
        pygame.draw.circle(self.screen, (160, 160, 140), (cx, skull_y), 7, 1)
        pygame.draw.circle(self.screen, (0, 0, 0), (cx - 3, skull_y - 1), 2)
        pygame.draw.circle(self.screen, (0, 0, 0), (cx + 3, skull_y - 1), 2)
        pygame.draw.line(self.screen, (0, 0, 0),
                         (cx - 2, skull_y + 4), (cx + 2, skull_y + 4), 1)

        spire_h = 12
        pygame.draw.polygon(self.screen, (70, 30, 80), [
            (cx - 4, by), (cx, by - spire_h), (cx + 4, by)
        ])

        orb_y = by - spire_h - 2
        glow = int(abs(math.sin(self.anim_tick * 0.1)) * 4)
        glow_surf = pygame.Surface((20 + glow * 2, 20 + glow * 2),
                                   pygame.SRCALPHA)
        gc = 10 + glow
        pygame.draw.circle(glow_surf, (100, 255, 80, 60), (gc, gc), gc)
        pygame.draw.circle(glow_surf, (150, 255, 120, 120), (gc, gc), gc // 2)
        self.screen.blit(glow_surf, (cx - gc, orb_y - gc))

        for i in range(3):
            a = self.anim_tick * 0.06 + i * 2.1
            sr = 14
            spx = int(cx + math.cos(a) * sr)
            spy = int(cy + math.sin(a) * sr)
            pygame.draw.circle(self.screen, (80, 200, 60, 150),
                               (spx, spy), 2)

        self._draw_tower_level_stars(cx, cy + ts // 4 + 8, tower.level)

    def _draw_tower_level_stars(self, cx, y, level):
        """Draw tiered star indicators: gold (1-5), orange (6-10), red (11-15)."""
        if level <= 5:
            tier_color = (255, 215, 50)
            display_count = level
        elif level <= 10:
            tier_color = (255, 140, 30)
            display_count = level - 5
        else:
            tier_color = (255, 50, 50)
            display_count = level - 10

        total_w = display_count * 10
        start_x = cx - total_w // 2
        for i in range(display_count):
            sx = start_x + i * 10 + 5
            self._draw_star(sx, y, 5, tier_color)

        if level > 5:
            tier_name = "II" if level <= 10 else "III"
            badge_color = (255, 140, 30) if level <= 10 else (255, 50, 50)
            badge = self.font_tiny.render(tier_name, True, badge_color)
            self.screen.blit(badge,
                             (cx - badge.get_width() // 2, y + 6))

    def _draw_star(self, cx, cy, size, color):
        """Draw a small 5-pointed star."""
        points = []
        for i in range(10):
            a = math.radians(36 * i - 90)
            r = size if i % 2 == 0 else size * 0.4
            points.append((int(cx + r * math.cos(a)),
                           int(cy + r * math.sin(a))))
        pygame.draw.polygon(self.screen, color, points)

    # ------------------------------------------------------------------
    # Projectiles
    # ------------------------------------------------------------------

    def _draw_projectiles(self, projectiles):
        """Draw projectiles with trails and glow effects."""
        for proj in projectiles:
            px, py = int(proj["x"]), int(proj["y"])
            tt = proj["tower_type"]

            if tt == TowerType.ARCHER:
                dx = proj["target_x"] - proj["x"]
                dy = proj["target_y"] - proj["y"]
                dist = math.sqrt(dx * dx + dy * dy)
                if dist > 0:
                    ndx, ndy = dx / dist, dy / dist
                    tail_x = int(px - ndx * 14)
                    tail_y = int(py - ndy * 14)
                    pygame.draw.line(self.screen, (100, 70, 25),
                                     (tail_x, tail_y), (px, py), 3)
                    pygame.draw.circle(self.screen, (255, 200, 60),
                                       (px, py), 4)
                    pygame.draw.circle(self.screen, (255, 240, 140),
                                       (px, py), 2)

            elif tt == TowerType.MAGE:
                glow = int(abs(math.sin(self.anim_tick * 0.2)) * 5)
                glow_r = 14 + glow
                glow_surf = pygame.Surface((glow_r * 2, glow_r * 2),
                                           pygame.SRCALPHA)
                pygame.draw.circle(glow_surf, (160, 60, 255, 80),
                                   (glow_r, glow_r), glow_r)
                pygame.draw.circle(glow_surf, (200, 120, 255, 140),
                                   (glow_r, glow_r), glow_r // 2)
                self.screen.blit(glow_surf, (px - glow_r, py - glow_r))
                pygame.draw.circle(self.screen, (230, 170, 255), (px, py), 6)
                pygame.draw.circle(self.screen, (255, 240, 255), (px, py), 3)
                for ti in range(4):
                    ta = self.anim_tick * 0.3 + ti * 1.57
                    spx = int(px + math.cos(ta) * 9)
                    spy = int(py + math.sin(ta) * 9)
                    pygame.draw.circle(self.screen, (220, 160, 255),
                                       (spx, spy), 2)

            elif tt == TowerType.ARTILLERY:
                pygame.draw.circle(self.screen, (60, 60, 65), (px, py), 7)
                pygame.draw.circle(self.screen, (40, 40, 45), (px, py), 7, 2)
                pygame.draw.circle(self.screen, (255, 140, 0), (px, py), 4)
                pygame.draw.circle(self.screen, (255, 220, 80), (px, py), 2)
                for si in range(3):
                    sa = self.anim_tick * 0.5 + si * 2.09
                    spx = int(px + math.cos(sa) * 6)
                    spy = int(py + math.sin(sa) * 6)
                    pygame.draw.circle(self.screen, (255, 200, 60),
                                       (spx, spy), 2)

            elif tt == TowerType.FREEZE:
                glow_surf = pygame.Surface((24, 24), pygame.SRCALPHA)
                pygame.draw.circle(glow_surf, (100, 200, 255, 80), (12, 12), 12)
                self.screen.blit(glow_surf, (px - 12, py - 12))
                pygame.draw.circle(self.screen, (160, 220, 255), (px, py), 5)
                pygame.draw.circle(self.screen, (230, 245, 255), (px, py), 3)
                for si in range(3):
                    sa = self.anim_tick * 0.25 + si * 2.09
                    spx = int(px + math.cos(sa) * 8)
                    spy = int(py + math.sin(sa) * 8)
                    pygame.draw.circle(self.screen, (200, 235, 255),
                                       (spx, spy), 2)

            elif tt == TowerType.POISON:
                glow_surf = pygame.Surface((22, 22), pygame.SRCALPHA)
                pygame.draw.circle(glow_surf, (80, 200, 40, 80), (11, 11), 11)
                self.screen.blit(glow_surf, (px - 11, py - 11))
                pygame.draw.circle(self.screen, (120, 220, 60), (px, py), 5)
                pygame.draw.circle(self.screen, (180, 255, 100), (px, py), 3)
                for si in range(3):
                    sa = self.anim_tick * 0.2 + si * 2.09
                    spx = int(px + math.cos(sa) * 7)
                    spy = int(py + math.sin(sa) * 7)
                    pygame.draw.circle(self.screen, (100, 220, 50),
                                       (spx, spy), 2)

            elif tt == TowerType.BALLISTA:
                dx = proj["target_x"] - proj["x"]
                dy = proj["target_y"] - proj["y"]
                dist = math.sqrt(dx * dx + dy * dy)
                if dist > 0:
                    ndx, ndy = dx / dist, dy / dist
                    tail_x = int(px - ndx * 18)
                    tail_y = int(py - ndy * 18)
                    pygame.draw.line(self.screen, (80, 55, 25),
                                     (tail_x, tail_y), (px, py), 4)
                    fletch_x = int(px - ndx * 14)
                    fletch_y = int(py - ndy * 14)
                    perp_x, perp_y = -ndy * 5, ndx * 5
                    pygame.draw.line(self.screen, (140, 100, 40),
                                     (int(fletch_x + perp_x),
                                      int(fletch_y + perp_y)),
                                     (int(fletch_x - perp_x),
                                      int(fletch_y - perp_y)), 2)
                    pygame.draw.circle(self.screen, (220, 180, 80),
                                       (px, py), 4)
                    pygame.draw.circle(self.screen, (255, 230, 140),
                                       (px, py), 2)

            elif tt == TowerType.NECROMANCER:
                glow_r = 12
                glow_surf = pygame.Surface((glow_r * 2, glow_r * 2),
                                           pygame.SRCALPHA)
                pygame.draw.circle(glow_surf, (80, 255, 60, 80),
                                   (glow_r, glow_r), glow_r)
                self.screen.blit(glow_surf, (px - glow_r, py - glow_r))
                pygame.draw.circle(self.screen, (100, 200, 80), (px, py), 5)
                pygame.draw.circle(self.screen, (160, 255, 120), (px, py), 3)
                skull_s = pygame.Surface((10, 10), pygame.SRCALPHA)
                pygame.draw.circle(skull_s, (200, 200, 180, 200), (5, 4), 4)
                pygame.draw.circle(skull_s, (0, 0, 0, 200), (3, 3), 1)
                pygame.draw.circle(skull_s, (0, 0, 0, 200), (7, 3), 1)
                self.screen.blit(skull_s, (px - 5, py - 5))

    # ------------------------------------------------------------------
    # Enemies
    # ------------------------------------------------------------------

    def _draw_enemies(self, enemies, colors):
        """Draw all living enemies."""
        for enemy in enemies:
            if not enemy.is_alive:
                continue
            cx, cy = int(enemy.x), int(enemy.y)
            is_hit = enemy.hit_timer > 0
            if enemy.enemy_type == EnemyType.GRUNT:
                self._draw_grunt(cx, cy, is_hit, enemy)
            elif enemy.enemy_type == EnemyType.RUNNER:
                self._draw_runner(cx, cy, is_hit, enemy)
            elif enemy.enemy_type == EnemyType.ARMORED:
                self._draw_armored(cx, cy, is_hit, enemy)
            elif enemy.enemy_type == EnemyType.BOMBER:
                self._draw_bomber(cx, cy, is_hit, enemy)
            elif enemy.enemy_type == EnemyType.BOSS:
                self._draw_boss(cx, cy, is_hit, enemy)
            if hasattr(enemy, 'slow_timer') and enemy.slow_timer > 0:
                slow_surf = pygame.Surface((22, 22), pygame.SRCALPHA)
                pygame.draw.circle(slow_surf, (100, 180, 255, 50),
                                   (11, 11), 11)
                self.screen.blit(slow_surf, (cx - 11, cy - 11))
            if hasattr(enemy, 'poison_timer') and enemy.poison_timer > 0:
                for pi in range(3):
                    pa = self.anim_tick * 0.15 + pi * 2.1
                    ppx = int(cx + math.cos(pa) * 12)
                    ppy = int(cy + math.sin(pa) * 12)
                    pygame.draw.circle(self.screen, (100, 220, 50),
                                       (ppx, ppy), 2)

            self._draw_health_bar(cx - 14, cy - 22, 28, 4,
                                  enemy.get_hp_ratio(), colors)

    def _draw_grunt(self, cx, cy, is_hit, enemy):
        """Draw a cartoon goblin grunt with bold outlines."""
        bob = int(math.sin(self.anim_tick * 0.15) * 2)
        outline = (35, 25, 15)

        foot_y = cy + 9 + bob
        step = int(math.sin(self.anim_tick * 0.3) * 3)
        foot_c = (85, 55, 30)
        for fx, fo in [(-4, step), (4, -step)]:
            pygame.draw.circle(self.screen, outline,
                               (cx + fx + fo, foot_y), 4)
            pygame.draw.circle(self.screen, foot_c,
                               (cx + fx + fo, foot_y), 3)

        body_c = (255, 130, 130) if is_hit else (115, 180, 75)
        body_dk = (255, 90, 90) if is_hit else (80, 140, 50)
        by = cy - 3 + bob
        pygame.draw.ellipse(self.screen, outline,
                            (cx - 9, by - 1, 18, 17))
        pygame.draw.ellipse(self.screen, body_c,
                            (cx - 7, by, 14, 14))
        pygame.draw.ellipse(self.screen, body_dk,
                            (cx - 4, by + 8, 8, 5))

        belt_y = by + 10
        pygame.draw.line(self.screen, (160, 130, 60),
                         (cx - 6, belt_y), (cx + 6, belt_y), 2)
        pygame.draw.circle(self.screen, (200, 170, 50), (cx, belt_y), 2)

        head_c = (255, 160, 160) if is_hit else (140, 200, 100)
        head_dk = (255, 120, 120) if is_hit else (100, 165, 70)
        head_y = cy - 9 + bob
        pygame.draw.circle(self.screen, outline, (cx, head_y), 9)
        pygame.draw.circle(self.screen, head_c, (cx, head_y), 7)
        pygame.draw.circle(self.screen, head_dk, (cx + 1, head_y + 2), 4)

        ear_pts_l = [(cx - 7, head_y - 1), (cx - 14, head_y - 7),
                     (cx - 6, head_y - 5)]
        ear_pts_r = [(cx + 7, head_y - 1), (cx + 14, head_y - 7),
                     (cx + 6, head_y - 5)]
        for pts in [ear_pts_l, ear_pts_r]:
            pygame.draw.polygon(self.screen, outline, pts)
            inner = [(p[0] + (1 if p[0] < cx else -1), p[1] + 1) for p in pts]
            pygame.draw.polygon(self.screen, head_c, inner)

        eye_ox = int(enemy.direction_x * 2)
        eye_oy = int(enemy.direction_y * 1.5)
        for ex in [-3, 3]:
            ex_pos = cx + ex + eye_ox
            ey_pos = head_y - 1 + eye_oy
            pygame.draw.circle(self.screen, (255, 255, 230),
                               (ex_pos, ey_pos), 3)
            pygame.draw.circle(self.screen, outline,
                               (ex_pos, ey_pos), 3, 1)
            pygame.draw.circle(self.screen, (20, 5, 0),
                               (ex_pos + 1, ey_pos), 1)

        mouth_y = head_y + 4
        pygame.draw.arc(self.screen, outline,
                        (cx - 3, mouth_y - 1, 6, 4),
                        math.pi, math.pi * 2, 1)

        weapon_x = cx + 8 + int(enemy.direction_x * 3)
        weapon_y = cy - 2 + bob
        swing = int(math.sin(self.anim_tick * 0.12) * 5)
        pygame.draw.line(self.screen, (120, 90, 50),
                         (weapon_x, weapon_y),
                         (weapon_x + 2, weapon_y - 10 + swing), 3)
        pygame.draw.line(self.screen, (160, 160, 170),
                         (weapon_x + 1, weapon_y - 8 + swing),
                         (weapon_x + 4, weapon_y - 13 + swing), 2)

    def _draw_runner(self, cx, cy, is_hit, enemy):
        """Draw a sleek wolf-like runner with bold cartoon outlines."""
        bob = int(math.sin(self.anim_tick * 0.4) * 3)
        outline = (40, 25, 10)
        body_c = (255, 220, 130) if is_hit else (195, 160, 90)
        body_dk = (255, 190, 80) if is_hit else (155, 120, 55)
        belly_c = (235, 215, 170) if is_hit else (220, 200, 150)

        body_pts = [
            (cx - 11, cy + 2 + bob),
            (cx - 5, cy - 7 + bob),
            (cx + 9, cy - 5 + bob),
            (cx + 13, cy + 2 + bob),
            (cx + 7, cy + 7 + bob),
            (cx - 7, cy + 7 + bob),
        ]
        pygame.draw.polygon(self.screen, outline, body_pts)
        inner_pts = [(p[0], p[1]) for p in body_pts]
        pygame.draw.polygon(self.screen, body_c,
                            [(p[0] + (1 if p[0] < cx else -1),
                              p[1] + (1 if p[1] < cy else -1))
                             for p in inner_pts])
        pygame.draw.ellipse(self.screen, belly_c,
                            (cx - 4, cy + 1 + bob, 10, 5))

        step = int(math.sin(self.anim_tick * 0.5) * 5)
        for lx, offset in [(-7, step), (-2, -step), (5, step), (9, -step)]:
            lx2 = cx + lx
            ly1 = cy + 6 + bob
            ly2 = cy + 12 + bob + offset
            pygame.draw.line(self.screen, outline,
                             (lx2, ly1), (lx2, ly2), 3)
            pygame.draw.line(self.screen, body_dk,
                             (lx2, ly1), (lx2, ly2), 2)
            pygame.draw.circle(self.screen, outline, (lx2, ly2), 2)

        tail_pts = [(cx + 12, cy + bob), (cx + 18, cy - 5 + bob),
                    (cx + 15, cy + 3 + bob)]
        pygame.draw.polygon(self.screen, outline, tail_pts)
        pygame.draw.polygon(self.screen, body_dk, tail_pts)

        head_x = cx - 9 + int(enemy.direction_x * 3)
        head_y = cy - 4 + bob
        pygame.draw.circle(self.screen, outline, (head_x, head_y), 7)
        pygame.draw.circle(self.screen, body_c, (head_x, head_y), 6)

        snout_pts = [(head_x - 5, head_y + 1), (head_x - 10, head_y + 3),
                     (head_x - 5, head_y + 4)]
        pygame.draw.polygon(self.screen, body_dk, snout_pts)
        pygame.draw.polygon(self.screen, outline, snout_pts, 1)
        pygame.draw.circle(self.screen, outline,
                           (head_x - 9, head_y + 2), 1)

        pygame.draw.circle(self.screen, (255, 240, 200),
                           (head_x - 2, head_y - 2), 3)
        pygame.draw.circle(self.screen, outline,
                           (head_x - 2, head_y - 2), 3, 1)
        pygame.draw.circle(self.screen, (180, 60, 20),
                           (head_x - 1, head_y - 2), 1)

        for side in [-1, 1]:
            ear_pts = [(head_x + side * 3, head_y - 5),
                       (head_x + side * 2, head_y - 12),
                       (head_x + side * 6, head_y - 6)]
            pygame.draw.polygon(self.screen, outline, ear_pts)
            pygame.draw.polygon(self.screen, body_c,
                                [(p[0], p[1] + 1) for p in ear_pts])

    def _draw_armored(self, cx, cy, is_hit, enemy):
        """Draw a heavily armored dark knight with bold outlines."""
        outline = (25, 25, 35)
        body_c = (220, 225, 255) if is_hit else (130, 135, 175)
        body_dk = (180, 185, 220) if is_hit else (95, 100, 140)
        armor_hl = (200, 205, 240) if is_hit else (165, 170, 210)

        foot_y = cy + 10
        step = int(math.sin(self.anim_tick * 0.12) * 2)
        boot_c = (75, 75, 100)
        for fx, fo in [(-6, step), (1, -step)]:
            pygame.draw.rect(self.screen, outline,
                             (cx + fx + fo - 1, foot_y - 4, 7, 7),
                             border_radius=1)
            pygame.draw.rect(self.screen, boot_c,
                             (cx + fx + fo, foot_y - 3, 5, 5),
                             border_radius=1)

        pygame.draw.rect(self.screen, outline,
                         (cx - 10, cy - 6, 20, 20), border_radius=3)
        pygame.draw.rect(self.screen, body_c,
                         (cx - 9, cy - 5, 18, 18), border_radius=2)
        pygame.draw.rect(self.screen, armor_hl,
                         (cx - 7, cy - 3, 14, 4), border_radius=1)
        for stripe_y in [cy + 1, cy + 7]:
            pygame.draw.line(self.screen, body_dk,
                             (cx - 7, stripe_y), (cx + 7, stripe_y), 1)

        pauldron_c = body_dk
        for side in [-1, 1]:
            px = cx + side * 10
            pygame.draw.circle(self.screen, outline, (px, cy - 2), 5)
            pygame.draw.circle(self.screen, pauldron_c, (px, cy - 2), 4)
            pygame.draw.circle(self.screen, armor_hl, (px - 1, cy - 3), 2)

        head_y = cy - 11
        pygame.draw.rect(self.screen, outline,
                         (cx - 7, head_y - 1, 14, 12), border_radius=3)
        pygame.draw.rect(self.screen, body_c,
                         (cx - 6, head_y, 12, 10), border_radius=2)
        plume_pts = [(cx, head_y - 1), (cx - 2, head_y - 7),
                     (cx + 4, head_y - 5)]
        pygame.draw.polygon(self.screen, (180, 40, 40), plume_pts)
        pygame.draw.polygon(self.screen, outline, plume_pts, 1)
        visor_y = head_y + 4
        pygame.draw.line(self.screen, outline,
                         (cx - 4, visor_y), (cx + 4, visor_y), 2)
        for vx in [-2, 2]:
            pygame.draw.circle(self.screen, (220, 60, 60),
                               (cx + vx, visor_y), 1)

        shield_x = cx - 13
        shield_y = cy - 3
        pygame.draw.rect(self.screen, outline,
                         (shield_x - 1, shield_y - 1, 8, 13),
                         border_radius=2)
        pygame.draw.rect(self.screen, (110, 110, 155),
                         (shield_x, shield_y, 6, 11), border_radius=1)
        pygame.draw.line(self.screen, (80, 80, 120),
                         (shield_x + 3, shield_y + 1),
                         (shield_x + 3, shield_y + 10), 1)
        pygame.draw.line(self.screen, (80, 80, 120),
                         (shield_x + 1, shield_y + 5),
                         (shield_x + 5, shield_y + 5), 1)

        sword_x = cx + 10
        swing = int(math.sin(self.anim_tick * 0.08) * 5)
        pygame.draw.line(self.screen, outline,
                         (sword_x, cy + 3), (sword_x + 2, cy - 12 + swing), 3)
        pygame.draw.line(self.screen, (210, 215, 225),
                         (sword_x, cy + 2), (sword_x + 2, cy - 11 + swing), 2)
        pygame.draw.circle(self.screen, (200, 180, 60),
                           (sword_x, cy + 3), 2)

    def _draw_boss(self, cx, cy, is_hit, enemy):
        """Draw a massive demon boss with detailed cartoon anatomy."""
        outline = (30, 5, 5)
        pulse = int(abs(math.sin(self.anim_tick * 0.04)) * 3)
        body_c = (255, 90, 90) if is_hit else (160, 30, 25)
        body_dk = (255, 55, 55) if is_hit else (120, 15, 12)
        body_hl = (255, 140, 140) if is_hit else (200, 65, 55)
        radius = 17 + pulse

        glow_r = radius + 12
        glow_surf = pygame.Surface((glow_r * 2, glow_r * 2), pygame.SRCALPHA)
        for gr in range(3):
            a = max(0, 40 - gr * 12)
            pygame.draw.circle(glow_surf, (220, 50, 30, a),
                               (glow_r, glow_r), glow_r - gr * 3)
        self.screen.blit(glow_surf, (cx - glow_r, cy - glow_r))

        foot_y = cy + radius - 2
        step = int(math.sin(self.anim_tick * 0.08) * 2)
        for fx, fo in [(-8, step), (8, -step)]:
            pygame.draw.circle(self.screen, outline,
                               (cx + fx + fo, foot_y + 4), 6)
            pygame.draw.circle(self.screen, body_dk,
                               (cx + fx + fo, foot_y + 4), 5)

        pygame.draw.circle(self.screen, outline, (cx, cy), radius + 2)
        pygame.draw.circle(self.screen, body_c, (cx, cy), radius)

        hl_surf = pygame.Surface((radius * 2, radius), pygame.SRCALPHA)
        pygame.draw.ellipse(hl_surf, (*body_hl, 60),
                            (2, 2, radius * 2 - 4, radius - 4))
        self.screen.blit(hl_surf, (cx - radius, cy - radius))

        belly = pygame.Rect(cx - radius + 5, cy + 2,
                            (radius - 5) * 2, radius - 6)
        belly_surf = pygame.Surface((belly.w, belly.h), pygame.SRCALPHA)
        pygame.draw.ellipse(belly_surf, (*body_dk, 80),
                            belly_surf.get_rect())
        self.screen.blit(belly_surf, belly.topleft)

        for side in [-1, 1]:
            arm_x = cx + side * (radius + 4)
            arm_y = cy + 2
            pygame.draw.circle(self.screen, outline, (arm_x, arm_y - 2), 6)
            pygame.draw.circle(self.screen, body_c, (arm_x, arm_y - 2), 5)
            fist_y = arm_y + 10 + int(math.sin(
                self.anim_tick * 0.06 + side) * 3)
            pygame.draw.line(self.screen, outline,
                             (arm_x, arm_y + 2), (arm_x, fist_y), 4)
            pygame.draw.line(self.screen, body_dk,
                             (arm_x, arm_y + 2), (arm_x, fist_y), 3)
            pygame.draw.circle(self.screen, outline,
                               (arm_x, fist_y), 5)
            pygame.draw.circle(self.screen, body_c,
                               (arm_x, fist_y), 4)

        horn_h = 14 + pulse
        for side in [-1, 1]:
            hx = cx + side * (radius - 4)
            pts = [
                (hx, cy - radius + 4),
                (hx + side * 8, cy - radius - horn_h),
                (hx + side * 2, cy - radius + 1)
            ]
            pygame.draw.polygon(self.screen, outline, pts)
            inner = [(p[0], p[1] + 1) for p in pts]
            pygame.draw.polygon(self.screen, (100, 20, 15), inner)
            ring_y = cy - radius - horn_h // 2
            pygame.draw.line(self.screen, (180, 150, 80),
                             (hx + side * 3, ring_y),
                             (hx + side * 6, ring_y), 2)

        for ex_off in [-7, 7]:
            ey = cy - 5
            e_x = cx + ex_off
            pygame.draw.ellipse(self.screen, outline,
                                (e_x - 5, ey - 4, 10, 8))
            pygame.draw.ellipse(self.screen, (255, 210, 50),
                                (e_x - 4, ey - 3, 8, 6))
            pupil_x = e_x + int(enemy.direction_x * 2)
            pygame.draw.circle(self.screen, (0, 0, 0),
                               (pupil_x, ey), 2)
            pygame.draw.circle(self.screen, (255, 255, 200),
                               (e_x - 2, ey - 2), 1)

        mouth_y = cy + 7
        pygame.draw.arc(self.screen, outline,
                        (cx - 10, mouth_y - 4, 20, 10),
                        math.pi, math.pi * 2, 2)
        for fx in [-5, -2, 1, 4]:
            pygame.draw.polygon(self.screen, (255, 255, 210), [
                (cx + fx, mouth_y - 1),
                (cx + fx + 1, mouth_y + 4),
                (cx + fx + 2, mouth_y - 1)
            ])

        crown_pts = []
        crown_base_y = cy - radius + 1
        crown_w = radius - 2
        spikes = 5
        for i in range(spikes * 2 + 1):
            x_off = -crown_w + i * crown_w // spikes
            if i % 2 == 0:
                crown_pts.append((cx + x_off, crown_base_y))
            else:
                crown_pts.append((cx + x_off, crown_base_y - 9 - pulse))
        if len(crown_pts) >= 3:
            pygame.draw.polygon(self.screen, outline, crown_pts)
            inner_cr = [(p[0], p[1] + 1) for p in crown_pts]
            pygame.draw.polygon(self.screen, (255, 210, 30), inner_cr)
            pygame.draw.polygon(self.screen, (200, 160, 0), inner_cr, 1)
            for i in range(1, len(crown_pts), 2):
                jx, jy = crown_pts[i]
                pygame.draw.circle(self.screen, (220, 50, 50),
                                   (jx, jy + 4), 2)
                pygame.draw.circle(self.screen, (255, 100, 100),
                                   (jx, jy + 3), 1)

    def _draw_bomber(self, cx, cy, is_hit, enemy):
        """Draw a goblin bomber carrying a TNT barrel with bold outlines."""
        outline = (35, 20, 10)
        bob = int(math.sin(self.anim_tick * 0.18) * 2)
        body_c = (255, 170, 90) if is_hit else (140, 100, 55)
        body_dk = (255, 130, 60) if is_hit else (105, 70, 35)
        skin_c = (255, 190, 130) if is_hit else (160, 120, 70)

        foot_y = cy + 9 + bob
        step = int(math.sin(self.anim_tick * 0.25) * 3)
        for fx, fo in [(-4, step), (4, -step)]:
            pygame.draw.circle(self.screen, outline,
                               (cx + fx + fo, foot_y), 4)
            pygame.draw.circle(self.screen, (80, 55, 30),
                               (cx + fx + fo, foot_y), 3)

        by = cy - 3 + bob
        pygame.draw.ellipse(self.screen, outline,
                            (cx - 9, by - 1, 18, 17))
        pygame.draw.ellipse(self.screen, body_c,
                            (cx - 7, by, 14, 14))
        pygame.draw.ellipse(self.screen, body_dk,
                            (cx - 4, by + 7, 8, 5))

        pygame.draw.line(self.screen, (180, 40, 30),
                         (cx - 6, by + 3), (cx + 6, by + 3), 2)

        head_y = cy - 9 + bob
        pygame.draw.circle(self.screen, outline, (cx, head_y), 9)
        pygame.draw.circle(self.screen, skin_c, (cx, head_y), 7)
        pygame.draw.circle(self.screen, body_dk, (cx + 1, head_y + 2), 4)

        ear_pts_l = [(cx - 7, head_y), (cx - 13, head_y - 5),
                     (cx - 6, head_y - 4)]
        ear_pts_r = [(cx + 7, head_y), (cx + 13, head_y - 5),
                     (cx + 6, head_y - 4)]
        for pts in [ear_pts_l, ear_pts_r]:
            pygame.draw.polygon(self.screen, outline, pts)
            pygame.draw.polygon(self.screen, skin_c,
                                [(p[0], p[1] + 1) for p in pts])

        bandana_pts = [(cx - 6, head_y - 5), (cx, head_y - 9),
                       (cx + 6, head_y - 5), (cx + 8, head_y - 8)]
        pygame.draw.polygon(self.screen, (180, 40, 30), bandana_pts)
        pygame.draw.polygon(self.screen, outline, bandana_pts, 1)

        eye_ox = int(enemy.direction_x * 2)
        for ex in [-3, 3]:
            pygame.draw.circle(self.screen, (255, 255, 230),
                               (cx + ex + eye_ox, head_y), 3)
            pygame.draw.circle(self.screen, outline,
                               (cx + ex + eye_ox, head_y), 3, 1)
            pygame.draw.circle(self.screen, (20, 5, 0),
                               (cx + ex + eye_ox + 1, head_y), 1)

        pygame.draw.arc(self.screen, outline,
                        (cx - 3, head_y + 3, 6, 4),
                        math.pi, math.pi * 2, 1)

        barrel_x = cx + 7
        barrel_y = cy - 2 + bob
        pygame.draw.rect(self.screen, outline,
                         (barrel_x - 4, barrel_y - 5, 9, 12),
                         border_radius=2)
        pygame.draw.rect(self.screen, (100, 65, 35),
                         (barrel_x - 3, barrel_y - 4, 7, 10),
                         border_radius=2)
        pygame.draw.line(self.screen, (70, 45, 20),
                         (barrel_x - 3, barrel_y), (barrel_x + 3, barrel_y), 1)
        pygame.draw.line(self.screen, (70, 45, 20),
                         (barrel_x - 3, barrel_y + 3),
                         (barrel_x + 3, barrel_y + 3), 1)

        txt_surf = self.font_tiny.render("X", True, (220, 50, 30))
        self.screen.blit(txt_surf,
                         (barrel_x - txt_surf.get_width() // 2,
                          barrel_y - 3))

        fuse_t = self.anim_tick * 0.2
        fuse_glow = int(abs(math.sin(fuse_t)) * 3)
        glow_r = 5 + fuse_glow
        glow_surf = pygame.Surface((glow_r * 2, glow_r * 2), pygame.SRCALPHA)
        pygame.draw.circle(glow_surf, (255, 180, 50, 80),
                           (glow_r, glow_r), glow_r)
        pygame.draw.circle(glow_surf, (255, 220, 100, 150),
                           (glow_r, glow_r), glow_r // 2)
        self.screen.blit(glow_surf,
                         (barrel_x - glow_r + 1, barrel_y - 6 - glow_r))
        pygame.draw.circle(self.screen, (255, 255, 200),
                           (barrel_x + 1, barrel_y - 6), 2)

    # ------------------------------------------------------------------
    # Soldiers
    # ------------------------------------------------------------------

    def _draw_soldiers(self, soldiers, colors):
        """Draw all living soldiers with detailed cartoon anatomy."""
        outline = (20, 20, 35)
        for soldier in soldiers:
            if not soldier.is_alive:
                continue
            cx, cy = int(soldier.x), int(soldier.y)
            self._draw_shadow(cx, cy + 6, 7)

            step = int(math.sin(self.anim_tick * 0.2) * 2) if soldier.target else 0
            for fx, fo in [(-3, step), (3, -step)]:
                pygame.draw.circle(self.screen, outline,
                                   (cx + fx + fo, cy + 9), 3)
                pygame.draw.circle(self.screen, (60, 45, 30),
                                   (cx + fx + fo, cy + 9), 2)

            armor_c = (55, 95, 200)
            armor_dk = (40, 70, 160)
            armor_hl = (90, 130, 230)
            pygame.draw.ellipse(self.screen, outline,
                                (cx - 7, cy - 3, 14, 15))
            pygame.draw.ellipse(self.screen, armor_c,
                                (cx - 6, cy - 2, 12, 13))
            pygame.draw.ellipse(self.screen, armor_hl,
                                (cx - 4, cy - 1, 8, 4))
            pygame.draw.line(self.screen, armor_dk,
                             (cx - 4, cy + 6), (cx + 4, cy + 6), 1)

            skin_c = (215, 185, 155)
            skin_dk = (185, 155, 125)
            head_y = cy - 7
            pygame.draw.circle(self.screen, outline, (cx, head_y), 6)
            pygame.draw.circle(self.screen, skin_c, (cx, head_y), 5)
            pygame.draw.circle(self.screen, skin_dk, (cx + 1, head_y + 1), 3)

            for ex in [-2, 2]:
                pygame.draw.circle(self.screen, (255, 255, 255),
                                   (cx + ex, head_y - 1), 2)
                pygame.draw.circle(self.screen, outline,
                                   (cx + ex, head_y - 1), 2, 1)
                pygame.draw.circle(self.screen, (15, 15, 40),
                                   (cx + ex, head_y - 1), 1)

            helmet_c = (175, 175, 190)
            helmet_dk = (130, 130, 145)
            helmet_pts = [(cx - 6, head_y - 1), (cx, head_y - 13),
                          (cx + 6, head_y - 1)]
            pygame.draw.polygon(self.screen, outline, helmet_pts)
            inner_h = [(cx - 5, head_y - 1), (cx, head_y - 12),
                       (cx + 5, head_y - 1)]
            pygame.draw.polygon(self.screen, helmet_c, inner_h)
            pygame.draw.line(self.screen, helmet_dk,
                             (cx, head_y - 12), (cx, head_y - 1), 1)
            pygame.draw.circle(self.screen, (220, 200, 80),
                               (cx, head_y - 10), 2)

            shield_x = cx - 9
            shield_y = cy - 4
            pygame.draw.rect(self.screen, outline,
                             (shield_x - 1, shield_y - 1, 7, 11),
                             border_radius=2)
            pygame.draw.rect(self.screen, (50, 80, 180),
                             (shield_x, shield_y, 5, 9), border_radius=1)
            pygame.draw.rect(self.screen, (80, 120, 220),
                             (shield_x + 1, shield_y + 1, 3, 3))
            pygame.draw.line(self.screen, (40, 60, 140),
                             (shield_x + 2, shield_y + 1),
                             (shield_x + 2, shield_y + 8), 1)

            sword_angle = self.anim_tick * 0.15 if soldier.target else 0.5
            sw_x = int(cx + 7 + math.cos(sword_angle) * 7)
            sw_y = int(cy - 5 + math.sin(sword_angle) * 7)
            pygame.draw.line(self.screen, outline,
                             (cx + 7, cy - 3), (sw_x, sw_y), 3)
            pygame.draw.line(self.screen, (220, 220, 235),
                             (cx + 7, cy - 3), (sw_x, sw_y), 2)
            pygame.draw.circle(self.screen, (220, 195, 80),
                               (cx + 7, cy - 3), 2)
            pygame.draw.circle(self.screen, outline,
                               (cx + 7, cy - 3), 2, 1)

            self._draw_health_bar(cx - 8, cy - 17, 16, 3,
                                  soldier.get_hp_ratio(), colors)

    # ------------------------------------------------------------------
    # Health bars
    # ------------------------------------------------------------------

    def _draw_health_bar(self, x, y, width, height, ratio, colors):
        """Draw a polished health bar with shine effect."""
        bg_rect = pygame.Rect(x - 1, y - 1, width + 2, height + 2)
        pygame.draw.rect(self.screen, (0, 0, 0), bg_rect, border_radius=1)
        fg_width = int(width * ratio)
        if ratio > 0.5:
            bar_color = (30, 200, 50)
        elif ratio > 0.25:
            bar_color = (240, 200, 30)
        else:
            bar_color = (240, 50, 30)
        if fg_width > 0:
            fg_rect = pygame.Rect(x, y, fg_width, height)
            pygame.draw.rect(self.screen, bar_color, fg_rect, border_radius=1)

    def _draw_tower_range(self, tower):
        """Draw a subtle attack range circle for a selected tower."""
        range_pixels = int(tower.attack_range * self.tile_size)
        range_surface = pygame.Surface(
            (range_pixels * 2, range_pixels * 2), pygame.SRCALPHA
        )
        pygame.draw.circle(range_surface, (255, 255, 255, 12),
                           (range_pixels, range_pixels), range_pixels)
        pygame.draw.circle(range_surface, (255, 255, 200, 45),
                           (range_pixels, range_pixels), range_pixels, 2)
        self.screen.blit(range_surface,
                         (tower.pixel_x - range_pixels,
                          tower.pixel_y - range_pixels))

    # ------------------------------------------------------------------
    # HUD (Kingdom Rush style — overlaid on map, no bottom panel)
    # ------------------------------------------------------------------

    def _draw_ui_panel(self, gold, base_hp, base_max_hp, round_number,
                       selected_tower_type, selected_tower, colors,
                       tower_unlocks=None, round_timer=0.0, game_speed=1,
                       base_level=1, selected_base=False, show_skip=False,
                       base_armor=0):
        """Draw the floating HUD elements overlaid on the game map."""
        screen_w = self.config["screen"]["width"]

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
        """Draw a warm semi-transparent rounded badge with golden border."""
        surf = pygame.Surface((w, h), pygame.SRCALPHA)
        pygame.draw.rect(surf, (15, 10, 5, 175), (0, 0, w, h),
                         border_radius=8)
        pygame.draw.rect(surf, (160, 130, 70, 140), (0, 0, w, h),
                         2, border_radius=8)
        hl = pygame.Surface((w - 6, h // 3), pygame.SRCALPHA)
        pygame.draw.rect(hl, (255, 240, 200, 15), hl.get_rect(),
                         border_radius=5)
        surf.blit(hl, (3, 2))
        self.screen.blit(surf, (x, y))

    def _draw_hud_top_left(self, base_hp, base_max_hp, gold, round_number,
                           base_armor=0):
        """Draw the top-left HUD: HP bar, armor, gold, wave counter."""
        badge_h = 92 if base_armor > 0 else 82
        self._draw_hud_badge(6, 6, 172, badge_h)

        pygame.draw.circle(self.screen, (220, 40, 40), (24, 20), 8)
        pygame.draw.circle(self.screen, (180, 20, 20), (24, 20), 8, 2)
        hp_text = self.font_medium.render(
            f"{base_hp}/{base_max_hp}", True, (255, 255, 255))
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
        if fg_w > 4:
            shine_surf = pygame.Surface((fg_w - 4, bar_h // 3), pygame.SRCALPHA)
            shine_surf.fill((255, 255, 255, 40))
            self.screen.blit(shine_surf, (bar_x + 2, bar_y + 2))
        pygame.draw.rect(self.screen, (180, 180, 180),
                         (bar_x, bar_y, bar_w, bar_h), 1, border_radius=4)

        info_y = 48
        if base_armor > 0:
            shield_cx, shield_cy = 24, info_y + 2
            pygame.draw.polygon(self.screen, (100, 140, 200), [
                (shield_cx, shield_cy - 7),
                (shield_cx - 6, shield_cy - 3),
                (shield_cx - 6, shield_cy + 3),
                (shield_cx, shield_cy + 7),
                (shield_cx + 6, shield_cy + 3),
                (shield_cx + 6, shield_cy - 3),
            ])
            pygame.draw.polygon(self.screen, (60, 100, 160), [
                (shield_cx, shield_cy - 7),
                (shield_cx - 6, shield_cy - 3),
                (shield_cx - 6, shield_cy + 3),
                (shield_cx, shield_cy + 7),
                (shield_cx + 6, shield_cy + 3),
                (shield_cx + 6, shield_cy - 3),
            ], 1)
            armor_txt = self.font_tiny.render(
                f"Armor {base_armor}", True, (160, 200, 255))
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
        wave_text = self.font_small.render(
            f"Round {round_number}", True, (255, 200, 100))
        self.screen.blit(wave_text, (14, badge_bottom + 3))

    def _draw_hud_top_right(self, game_speed, round_timer, show_skip=False):
        """Draw the top-right HUD: pause, speed, timer, and skip button."""
        screen_w = self.config["screen"]["width"]
        mouse = pygame.mouse.get_pos()

        pause_r = self.get_pause_button_rect()
        ph = pause_r.collidepoint(mouse)
        bg = (60, 60, 80, 200) if ph else (30, 30, 45, 180)
        surf = pygame.Surface((pause_r.width, pause_r.height), pygame.SRCALPHA)
        pygame.draw.rect(surf, bg, (0, 0, pause_r.width, pause_r.height),
                         border_radius=6)
        self.screen.blit(surf, pause_r)
        pygame.draw.rect(self.screen, (140, 140, 160), pause_r, 1,
                         border_radius=6)
        cx, cy = pause_r.centerx, pause_r.centery
        pygame.draw.rect(self.screen, (220, 220, 240),
                         (cx - 5, cy - 7, 4, 14))
        pygame.draw.rect(self.screen, (220, 220, 240),
                         (cx + 1, cy - 7, 4, 14))

        speed_r = self.get_speed_button_rect()
        sh = speed_r.collidepoint(mouse)
        speed_colors = {1: (140, 140, 160), 2: (220, 200, 60), 3: (255, 100, 60)}
        sc = speed_colors.get(game_speed, (140, 140, 160))
        sbg = (60, 60, 80, 200) if sh else (30, 30, 45, 180)
        surf2 = pygame.Surface((speed_r.width, speed_r.height), pygame.SRCALPHA)
        pygame.draw.rect(surf2, sbg, (0, 0, speed_r.width, speed_r.height),
                         border_radius=6)
        self.screen.blit(surf2, speed_r)
        pygame.draw.rect(self.screen, sc, speed_r, 1, border_radius=6)
        label = self.font_small.render(f"x{game_speed}", True, sc)
        self.screen.blit(label, label.get_rect(center=speed_r.center))

        minutes = int(round_timer) // 60
        seconds = int(round_timer) % 60
        timer_text = self.font_tiny.render(
            f"{minutes:02d}:{seconds:02d}", True, (180, 180, 200))
        self.screen.blit(timer_text, (screen_w - 48, 44))

        if show_skip:
            skip_r = self.get_skip_button_rect()
            if skip_r is not None:
                skh = skip_r.collidepoint(mouse)
                pulse = abs(math.sin(self.anim_tick * 0.08))
                sk_bg = (180, 60, 30, 220) if skh else (120, 40, 20, int(160 + pulse * 60))
                sk_surf = pygame.Surface((skip_r.width, skip_r.height),
                                         pygame.SRCALPHA)
                pygame.draw.rect(sk_surf, sk_bg,
                                 (0, 0, skip_r.width, skip_r.height),
                                 border_radius=8)
                self.screen.blit(sk_surf, skip_r)
                pygame.draw.rect(self.screen, (255, 140, 80), skip_r, 2,
                                 border_radius=8)
                sk_label = self.font_small.render("SKIP >>", True,
                                                   (255, 230, 180))
                self.screen.blit(sk_label,
                                 sk_label.get_rect(center=skip_r.center))

    def _draw_radial_menu(self, tower, gold):
        """Draw Kingdom Rush-style radial upgrade/sell buttons around a tower."""
        cx, cy = tower.pixel_x, tower.pixel_y
        ring_r = self.tile_size // 2 + 16

        ring_surf = pygame.Surface((ring_r * 2 + 4, ring_r * 2 + 4),
                                   pygame.SRCALPHA)
        pygame.draw.circle(ring_surf, (0, 0, 0, 80),
                           (ring_r + 2, ring_r + 2), ring_r, 3)
        self.screen.blit(ring_surf, (cx - ring_r - 2, cy - ring_r - 2))

        upg_rect = self.get_upgrade_button_rect(tower)
        sell_rect = self.get_sell_button_rect(tower)
        mouse = pygame.mouse.get_pos()

        upgrade_cost = tower.get_upgrade_cost()
        if upgrade_cost > 0:
            uh = upg_rect.collidepoint(mouse)
            can_afford = gold >= upgrade_cost
            bg = (40, 100, 40, 210) if (uh and can_afford) else (30, 30, 35, 200)
            s = pygame.Surface((upg_rect.width, upg_rect.height), pygame.SRCALPHA)
            pygame.draw.rect(s, bg, (0, 0, upg_rect.width, upg_rect.height),
                             border_radius=6)
            self.screen.blit(s, upg_rect)
            border_c = (100, 220, 100) if can_afford else (70, 70, 80)
            pygame.draw.rect(self.screen, border_c, upg_rect, 2,
                             border_radius=6)
            arrow_cx, arrow_cy = upg_rect.centerx, upg_rect.centery - 4
            pygame.draw.polygon(self.screen, (220, 255, 220), [
                (arrow_cx, arrow_cy - 8),
                (arrow_cx - 7, arrow_cy + 2),
                (arrow_cx + 7, arrow_cy + 2)])
            cost_c = (255, 215, 0) if can_afford else (100, 80, 40)
            cost_txt = self.font_tiny.render(str(upgrade_cost), True, cost_c)
            self.screen.blit(cost_txt,
                             cost_txt.get_rect(center=(upg_rect.centerx,
                                                       upg_rect.centery + 10)))

        slh = sell_rect.collidepoint(mouse)
        sbg = (120, 90, 20, 210) if slh else (30, 30, 35, 200)
        s2 = pygame.Surface((sell_rect.width, sell_rect.height), pygame.SRCALPHA)
        pygame.draw.rect(s2, sbg, (0, 0, sell_rect.width, sell_rect.height),
                         border_radius=6)
        self.screen.blit(s2, sell_rect)
        pygame.draw.rect(self.screen, (200, 180, 60), sell_rect, 2,
                         border_radius=6)
        sell_sym = self.font_medium.render("$", True, (255, 215, 0))
        self.screen.blit(sell_sym,
                         sell_sym.get_rect(center=(sell_rect.centerx,
                                                   sell_rect.centery - 2)))
        sell_val = self.font_tiny.render(
            str(tower.get_sell_value()), True, (200, 200, 160))
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
        line_h = 14
        total_h = line_h * len(lines) + 6
        max_w = 0
        rendered = []
        for line in lines:
            txt = self.font_tiny.render(line, True, (255, 255, 220))
            rendered.append(txt)
            max_w = max(max_w, txt.get_width())

        info_bg = pygame.Surface((max_w + 12, total_h), pygame.SRCALPHA)
        info_bg.fill((0, 0, 0, 160))
        bg_x = cx - (max_w + 12) // 2
        self.screen.blit(info_bg, (bg_x, info_y - 2))
        pygame.draw.rect(self.screen, (100, 100, 120),
                         (bg_x, info_y - 2, max_w + 12, total_h), 1,
                         border_radius=3)
        for i, txt in enumerate(rendered):
            self.screen.blit(txt,
                             txt.get_rect(center=(cx, info_y + 5 + i * line_h)))

    def _draw_base_radial(self, base_level, gold):
        """Draw radial upgrade button around the base castle."""
        if self._base_wp is None:
            return
        bx, by = self._base_wp
        ring_r = self.tile_size // 2 + 16
        ring_surf = pygame.Surface((ring_r * 2 + 4, ring_r * 2 + 4),
                                   pygame.SRCALPHA)
        pygame.draw.circle(ring_surf, (255, 200, 50, 60),
                           (ring_r + 2, ring_r + 2), ring_r, 3)
        self.screen.blit(ring_surf, (bx - ring_r - 2, by - ring_r - 2))

        upg_rect = self.get_base_upgrade_button_rect()
        if upg_rect is None:
            return
        mouse = pygame.mouse.get_pos()
        max_lvl = len(self.config["gameplay"]["base_upgrade_cost"])
        if base_level < max_lvl:
            cost = self.config["gameplay"]["base_upgrade_cost"][base_level]
            can_afford = gold >= cost
            uh = upg_rect.collidepoint(mouse)
            bg = (40, 100, 40, 210) if (uh and can_afford) else (30, 30, 35, 200)
            s = pygame.Surface((upg_rect.width, upg_rect.height), pygame.SRCALPHA)
            pygame.draw.rect(s, bg, (0, 0, upg_rect.width, upg_rect.height),
                             border_radius=6)
            self.screen.blit(s, upg_rect)
            border_c = (100, 220, 100) if can_afford else (70, 70, 80)
            pygame.draw.rect(self.screen, border_c, upg_rect, 2,
                             border_radius=6)
            arrow_cx, arrow_cy = upg_rect.centerx, upg_rect.centery - 4
            pygame.draw.polygon(self.screen, (220, 255, 220), [
                (arrow_cx, arrow_cy - 8),
                (arrow_cx - 7, arrow_cy + 2),
                (arrow_cx + 7, arrow_cy + 2)])
            cost_c = (255, 215, 0) if can_afford else (100, 80, 40)
            cost_txt = self.font_tiny.render(str(cost), True, cost_c)
            self.screen.blit(cost_txt,
                             cost_txt.get_rect(center=(upg_rect.centerx,
                                                       upg_rect.centery + 10)))
        else:
            s = pygame.Surface((upg_rect.width, upg_rect.height), pygame.SRCALPHA)
            pygame.draw.rect(s, (30, 30, 35, 200),
                             (0, 0, upg_rect.width, upg_rect.height),
                             border_radius=6)
            self.screen.blit(s, upg_rect)
            pygame.draw.rect(self.screen, (70, 70, 80), upg_rect, 2,
                             border_radius=6)
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
        line1 = self.font_small.render(f"{name} ({cost}g)", True, (255, 255, 220))
        line2 = self.font_tiny.render(desc, True, (180, 200, 160))
        w = max(line1.get_width(), line2.get_width()) + 12
        h = line1.get_height() + line2.get_height() + 8
        screen_w = self.config["screen"]["width"]
        if tx + w > screen_w:
            tx = mouse[0] - w - 8
        bg = pygame.Surface((w, h), pygame.SRCALPHA)
        bg.fill((0, 0, 0, 170))
        self.screen.blit(bg, (tx, ty))
        self.screen.blit(line1, (tx + 6, ty + 3))
        self.screen.blit(line2, (tx + 6, ty + 3 + line1.get_height()))

    def _draw_tower_bar(self, selected_tower_type, gold, tower_unlocks=None):
        """Draw tower purchase icons at the bottom-center of the screen."""
        tower_types = [
            TowerType.ARCHER, TowerType.BARRACKS, TowerType.MAGE,
            TowerType.ARTILLERY, TowerType.FREEZE, TowerType.POISON,
            TowerType.BALLISTA, TowerType.TESLA, TowerType.NECROMANCER,
            TowerType.LASER,
        ]
        icon_colors = [
            (0, 160, 40), (60, 90, 160), (140, 60, 200),
            (180, 130, 30), (100, 180, 240), (80, 180, 50),
            (160, 120, 40), (60, 100, 220), (100, 50, 120),
            (220, 60, 60),
        ]
        screen_w = self.config["screen"]["width"]
        screen_h = self.config["screen"]["height"]
        btn_size = 40
        gap = 4
        total_w = len(tower_types) * btn_size + (len(tower_types) - 1) * gap
        start_x = (screen_w - total_w) // 2
        bar_y = screen_h - btn_size - 10

        bar_bg = pygame.Surface((total_w + 16, btn_size + 12), pygame.SRCALPHA)
        pygame.draw.rect(bar_bg, (15, 12, 8, 170),
                         (0, 0, total_w + 16, btn_size + 12), border_radius=8)
        pygame.draw.rect(bar_bg, (140, 115, 65, 120),
                         (0, 0, total_w + 16, btn_size + 12),
                         2, border_radius=8)
        self.screen.blit(bar_bg, (start_x - 8, bar_y - 6))

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
                bg_c = (35, 30, 25)
                brd = (65, 55, 45)
            elif selected_tower_type == t_type:
                bg_c = (60, 120, 190)
                brd = (130, 200, 255)
            elif hovering and can_afford:
                bg_c = (70, 62, 48)
                brd = (140, 120, 85)
            elif can_afford:
                bg_c = (50, 44, 35)
                brd = (100, 88, 65)
            else:
                bg_c = (38, 33, 28)
                brd = (70, 60, 48)

            pygame.draw.rect(self.screen, bg_c, rect, border_radius=6)
            pygame.draw.rect(self.screen, brd, rect, 2, border_radius=6)

            icx, icy = x + btn_size // 2, y + btn_size // 2 - 4
            ic = icon_colors[i] if unlocked else (40, 40, 40)
            if not unlocked:
                lock_r = self.config["tower_unlocks"].get(t_type, "?")
                lt = self.font_tiny.render(f"R{lock_r}", True, (160, 120, 80))
                self.screen.blit(lt, lt.get_rect(center=(icx, icy)))
            else:
                self._draw_tower_icon(t_type, icx, icy, ic)

            cost_c = (255, 215, 50) if can_afford else (120, 100, 55)
            if not unlocked:
                cost_c = (100, 80, 55)
            ct = self.font_tiny.render(f"{cost}", True, cost_c)
            self.screen.blit(ct,
                             ct.get_rect(center=(x + btn_size // 2,
                                                 y + btn_size - 5)))

    def _draw_tower_icon(self, t_type, icx, icy, ic):
        """Draw a small tower icon in a button."""
        if t_type == TowerType.ARCHER:
            pygame.draw.rect(self.screen, ic,
                             (icx - 5, icy - 6, 10, 12), border_radius=1)
            pygame.draw.polygon(self.screen, (0, min(255, ic[1] + 40), 0),
                                [(icx - 6, icy - 4), (icx, icy - 10),
                                 (icx + 6, icy - 4)])
        elif t_type == TowerType.MAGE:
            pts = [(icx, icy - 10), (icx - 7, icy + 6),
                   (icx + 7, icy + 6)]
            pygame.draw.polygon(self.screen, ic, pts)
            pygame.draw.circle(self.screen, (220, 180, 255),
                               (icx, icy - 8), 3)
        elif t_type == TowerType.ARTILLERY:
            pygame.draw.rect(self.screen, ic,
                             (icx - 7, icy - 3, 14, 8), border_radius=2)
            pygame.draw.line(self.screen, (80, 80, 80),
                             (icx, icy), (icx + 10, icy - 4), 3)
        elif t_type == TowerType.BARRACKS:
            pygame.draw.rect(self.screen, ic,
                             (icx - 7, icy - 6, 14, 12), border_radius=2)
            pygame.draw.circle(self.screen, (200, 200, 60),
                               (icx, icy), 4)
        elif t_type == TowerType.FREEZE:
            pygame.draw.polygon(self.screen, ic,
                                [(icx, icy - 10), (icx - 6, icy + 4),
                                 (icx + 6, icy + 4)])
            pygame.draw.circle(self.screen, (220, 240, 255),
                               (icx, icy - 6), 3)
        elif t_type == TowerType.POISON:
            pygame.draw.circle(self.screen, ic, (icx, icy), 8)
            pygame.draw.circle(self.screen, (200, 255, 100),
                               (icx, icy - 2), 3)
        elif t_type == TowerType.BALLISTA:
            pygame.draw.line(self.screen, ic,
                             (icx - 8, icy), (icx + 8, icy), 3)
            pygame.draw.line(self.screen, (min(255, ic[0] + 40), ic[1], ic[2]),
                             (icx, icy), (icx + 10, icy - 3), 2)
            pygame.draw.circle(self.screen, (200, 160, 60),
                               (icx + 10, icy - 3), 2)
        elif t_type == TowerType.TESLA:
            pygame.draw.rect(self.screen, ic,
                             (icx - 4, icy - 6, 8, 14), border_radius=2)
            pygame.draw.circle(self.screen, (150, 200, 255),
                               (icx, icy - 6), 4)
            pygame.draw.line(self.screen, (100, 180, 255),
                             (icx, icy - 6), (icx - 6, icy - 10), 1)
            pygame.draw.line(self.screen, (100, 180, 255),
                             (icx, icy - 6), (icx + 6, icy - 10), 1)
        elif t_type == TowerType.NECROMANCER:
            pts = [(icx, icy - 10), (icx - 7, icy + 6),
                   (icx + 7, icy + 6)]
            pygame.draw.polygon(self.screen, ic, pts)
            pygame.draw.circle(self.screen, (200, 200, 180),
                               (icx, icy - 2), 4)
            pygame.draw.circle(self.screen, (0, 0, 0), (icx - 1, icy - 3), 1)
            pygame.draw.circle(self.screen, (0, 0, 0), (icx + 1, icy - 3), 1)
        elif t_type == TowerType.LASER:
            pygame.draw.rect(self.screen, ic,
                             (icx - 5, icy - 8, 10, 16), border_radius=2)
            pygame.draw.circle(self.screen, (255, 100, 100),
                               (icx, icy - 6), 4)

    def _draw_tower_info(self, tower, colors, panel_top):
        """No-op: tower info is now shown via radial menu."""
        pass

    def _draw_tower_type_tooltip(self, tower_type, panel_top):
        """No-op: tooltip is now drawn via _draw_placement_tooltip near cursor."""
        pass

    # ------------------------------------------------------------------
    # Overlay screens
    # ------------------------------------------------------------------

    def _draw_overlay_bg(self, alpha=160):
        """Draw a warm dark semi-transparent overlay."""
        sw = self.config["screen"]["width"]
        sh = self.config["screen"]["height"]
        overlay = pygame.Surface((sw, sh), pygame.SRCALPHA)
        overlay.fill((10, 8, 5, alpha))
        self.screen.blit(overlay, (0, 0))

    def _draw_decorative_frame(self, rect, border_color, fill_color):
        """Draw a warm rounded decorative frame with golden trim."""
        shadow = rect.inflate(4, 4).move(2, 2)
        s_surf = pygame.Surface((shadow.w, shadow.h), pygame.SRCALPHA)
        pygame.draw.rect(s_surf, (0, 0, 0, 60), s_surf.get_rect(),
                         border_radius=14)
        self.screen.blit(s_surf, shadow.topleft)
        pygame.draw.rect(self.screen, fill_color, rect, border_radius=12)
        pygame.draw.rect(self.screen, border_color, rect, 3, border_radius=12)
        inner = rect.inflate(-8, -8)
        lighter = tuple(min(255, c + 30) for c in border_color)
        pygame.draw.rect(self.screen, lighter, inner, 1, border_radius=10)
        hl = pygame.Surface((rect.w - 12, rect.h // 4), pygame.SRCALPHA)
        pygame.draw.rect(hl, (255, 245, 210, 12), hl.get_rect(),
                         border_radius=8)
        self.screen.blit(hl, (rect.x + 6, rect.y + 4))

    def _draw_button(self, rect, text, bg_color, hover_color, border_color):
        """Draw a styled button with hover detection.

        Returns:
            True if the mouse is hovering over this button.
        """
        mouse_pos = pygame.mouse.get_pos()
        hovering = rect.collidepoint(mouse_pos)
        color = hover_color if hovering else bg_color
        pygame.draw.rect(self.screen, color, rect, border_radius=8)
        pygame.draw.rect(self.screen, border_color, rect, 2, border_radius=8)

        shine = pygame.Rect(rect.x + 4, rect.y + 3,
                            rect.width - 8, rect.height // 3)
        shine_surf = pygame.Surface((shine.width, shine.height),
                                    pygame.SRCALPHA)
        shine_surf.fill((255, 255, 255, 25))
        self.screen.blit(shine_surf, shine)

        btn_text = self.font_medium.render(text, True, (255, 255, 255))
        btn_text_rect = btn_text.get_rect(center=rect.center)
        shadow = self.font_medium.render(text, True, (0, 0, 0))
        self.screen.blit(shadow,
                         (btn_text_rect.x + 1, btn_text_rect.y + 1))
        self.screen.blit(btn_text, btn_text_rect)
        return hovering

    def draw_menu(self):
        """Draw a warm, medieval-themed main menu screen."""
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
        self.screen.blit(shadow,
                         shadow.get_rect(center=(sw // 2 + 3, 173)))
        title = self.font_title.render("Tower Defense", True, (255, 215, 80))
        self.screen.blit(title,
                         title.get_rect(center=(sw // 2, 170)))

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
            self.screen.blit(
                ctrl_text,
                ctrl_text.get_rect(center=(sw // 2, 380 + i * 24))
            )

    def draw_round_complete(self, round_number, bonus_gold):
        """Draw the round complete overlay."""
        sw = self.config["screen"]["width"]
        sh = self.config["screen"]["height"]
        self.anim_tick += 1
        self._draw_overlay_bg(160)

        frame_w = min(560, sw - 40)
        frame = pygame.Rect(sw // 2 - frame_w // 2, sh // 2 - 130,
                            frame_w, 260)
        self._draw_decorative_frame(frame, (60, 180, 60), (15, 30, 15))

        title = self.font_large.render(
            f"Round {round_number} Complete!", True, (100, 255, 100)
        )
        self.screen.blit(title,
                         title.get_rect(center=(sw // 2, sh // 2 - 75)))

        bonus = self.font_medium.render(
            f"+{bonus_gold} Gold Bonus!", True, (255, 215, 0)
        )
        self.screen.blit(bonus,
                         bonus.get_rect(center=(sw // 2, sh // 2 - 20)))

        btn_w = min(340, frame_w - 40)
        btn = pygame.Rect(sw // 2 - btn_w // 2, sh // 2 + 30, btn_w, 50)
        self._draw_button(btn,
                          f"Next Round ({round_number + 1}) [SPACE]",
                          (40, 140, 40), (60, 180, 60), (100, 220, 100))

    def draw_round_failed(self, round_number):
        """Draw the round failed overlay."""
        sw = self.config["screen"]["width"]
        sh = self.config["screen"]["height"]
        self.anim_tick += 1
        self._draw_overlay_bg(180)

        frame_w = min(560, sw - 40)
        frame = pygame.Rect(sw // 2 - frame_w // 2, sh // 2 - 140,
                            frame_w, 320)
        self._draw_decorative_frame(frame, (180, 60, 60), (30, 12, 12))

        title = self.font_large.render(
            "Base Destroyed!", True, (255, 80, 80)
        )
        self.screen.blit(title,
                         title.get_rect(center=(sw // 2, sh // 2 - 90)))

        info = self.font_medium.render(
            f"Round {round_number} — Castle overrun!",
            True, (200, 200, 200)
        )
        self.screen.blit(info,
                         info.get_rect(center=(sw // 2, sh // 2 - 35)))

        btn_w = min(340, frame_w - 40)
        retry_btn = pygame.Rect(sw // 2 - btn_w // 2, sh // 2 + 10,
                                btn_w, 50)
        self._draw_button(retry_btn,
                          f"Retry Round {round_number} [R]",
                          (140, 90, 30), (180, 120, 40), (220, 160, 60))

        restart_btn = pygame.Rect(sw // 2 - btn_w // 2, sh // 2 + 80,
                                  btn_w, 50)
        self._draw_button(restart_btn, "Full Restart",
                          (50, 50, 70), (70, 70, 90), (110, 110, 130))

    def draw_game_over(self, highest_round):
        """Draw the game over screen."""
        sw = self.config["screen"]["width"]
        sh = self.config["screen"]["height"]
        self.anim_tick += 1

        for y in range(sh):
            ratio = y / sh
            r = int(30 + ratio * 10)
            g = int(8 + ratio * 5)
            b = int(8 + ratio * 5)
            pygame.draw.line(self.screen, (r, g, b), (0, y), (sw, y))

        frame_w = min(560, sw - 40)
        frame = pygame.Rect(sw // 2 - frame_w // 2, 120, frame_w, 350)
        self._draw_decorative_frame(frame, (160, 40, 40), (25, 8, 8))

        title = self.font_large.render("GAME OVER", True, (220, 40, 40))
        self.screen.blit(title,
                         title.get_rect(center=(sw // 2, 190)))

        info = self.font_medium.render(
            f"Highest round reached: {highest_round}",
            True, (200, 200, 200)
        )
        self.screen.blit(info, info.get_rect(center=(sw // 2, 270)))

        btn_w = min(340, frame_w - 40)
        btn = pygame.Rect(sw // 2 - btn_w // 2, 340, btn_w, 50)
        self._draw_button(btn, "Restart [R]",
                          (60, 140, 60), (80, 180, 80), (120, 220, 120))

    def draw_pause_overlay(self):
        """Draw a pause overlay."""
        sw = self.config["screen"]["width"]
        sh = self.config["screen"]["height"]
        self._draw_overlay_bg(150)

        frame = pygame.Rect(sw // 2 - 160, sh // 2 - 60, 320, 120)
        self._draw_decorative_frame(frame, (100, 100, 120), (20, 20, 30))

        text = self.font_title.render("PAUSED", True, (255, 255, 255))
        self.screen.blit(text,
                         text.get_rect(center=(sw // 2, sh // 2 - 15)))

        hint = self.font_medium.render(
            "Press [P] to resume", True, (170, 170, 180)
        )
        self.screen.blit(hint,
                         hint.get_rect(center=(sw // 2, sh // 2 + 30)))

    # ------------------------------------------------------------------
    # Button rect helpers
    # ------------------------------------------------------------------

    def _get_centered_button_rect(self, y_top):
        """Get a centered button rectangle."""
        sw = self.config["screen"]["width"]
        btn_w, btn_h = 340, 50
        return pygame.Rect(sw // 2 - btn_w // 2, y_top, btn_w, btn_h)

    def get_tower_button_rects(self):
        """Get clickable rectangles for the bottom tower bar."""
        tower_types = [
            TowerType.ARCHER, TowerType.BARRACKS, TowerType.MAGE,
            TowerType.ARTILLERY, TowerType.FREEZE, TowerType.POISON,
            TowerType.BALLISTA, TowerType.TESLA, TowerType.NECROMANCER,
            TowerType.LASER,
        ]
        screen_w = self.config["screen"]["width"]
        screen_h = self.config["screen"]["height"]
        btn_size = 40
        gap = 4
        total_w = len(tower_types) * btn_size + (len(tower_types) - 1) * gap
        start_x = (screen_w - total_w) // 2
        bar_y = screen_h - btn_size - 10

        buttons = []
        for i, t_type in enumerate(tower_types):
            x = start_x + i * (btn_size + gap)
            rect = pygame.Rect(x, bar_y, btn_size, btn_size)
            buttons.append((t_type, rect))
        return buttons

    def get_upgrade_button_rect(self, tower):
        """Get the radial upgrade button rect above a tower."""
        cx, cy = tower.pixel_x, tower.pixel_y
        btn_w, btn_h = 40, 34
        ring_r = self.tile_size // 2 + 16
        return pygame.Rect(cx - btn_w // 2, cy - ring_r - btn_h // 2,
                           btn_w, btn_h)

    def get_sell_button_rect(self, tower):
        """Get the radial sell button rect below a tower."""
        cx, cy = tower.pixel_x, tower.pixel_y
        btn_w, btn_h = 40, 34
        ring_r = self.tile_size // 2 + 16
        return pygame.Rect(cx - btn_w // 2, cy + ring_r - btn_h // 2,
                           btn_w, btn_h)

    def get_base_upgrade_button_rect(self):
        """Get the radial upgrade button rect above the base castle."""
        wp = getattr(self, "_base_wp", None)
        if wp is None:
            return None
        bx, by = wp
        btn_w, btn_h = 40, 34
        ring_r = self.tile_size // 2 + 16
        return pygame.Rect(bx - btn_w // 2, by - ring_r - btn_h // 2,
                           btn_w, btn_h)

    def get_next_round_button_rect(self):
        """Get the 'Next Round' button rectangle."""
        sh = self.config["screen"]["height"]
        return self._get_centered_button_rect(sh // 2 + 30)

    def get_retry_button_rect(self):
        """Get the 'Retry' button rectangle."""
        sh = self.config["screen"]["height"]
        return self._get_centered_button_rect(sh // 2 + 10)

    def get_restart_button_rect(self):
        """Get the 'Restart' button rectangle."""
        return self._get_centered_button_rect(340)

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
