"""Mixin for drawing game entities: towers, enemies, soldiers, projectiles."""

import math
import random
import pygame
from enums import TowerType


class RendererEntitiesMixin:
    """Mixin providing tower, enemy, soldier, and projectile drawing."""

    def _draw_towers(self, towers):
        """Draw all towers using sprite assets."""
        for tower in towers:
            cx, cy = tower.pixel_x, tower.pixel_y

            base_sprite = self.assets.tower_base_main
            bw, bh = base_sprite.get_size()
            self.screen.blit(base_sprite, (cx - bw // 2, cy - bh // 2 + 4))

            sprite = self.assets.towers.get(tower.tower_type)
            if sprite is not None:
                level_scale = 1.0 + tower.level * 0.02
                sw_t = int(sprite.get_width() * level_scale)
                sh_t = int(sprite.get_height() * level_scale)
                scaled = pygame.transform.scale(sprite, (sw_t, sh_t))

                _ROTATABLE = {TowerType.ARCHER, TowerType.ARTILLERY,
                              TowerType.BALLISTA, TowerType.FORTRESS}
                if (tower.target and tower.target.is_alive
                        and tower.tower_type in _ROTATABLE):
                    dx = tower.target.x - cx
                    dy = tower.target.y - cy
                    angle = -math.degrees(math.atan2(dy, dx)) - 90
                    scaled = pygame.transform.rotate(scaled, angle)
                    scaled.set_colorkey((255, 0, 255))

                sw_t, sh_t = scaled.get_size()
                self.screen.blit(scaled, (cx - sw_t // 2, cy - sh_t // 2 - 4))

            self._draw_tower_level_stars(cx, cy + self.tile_size // 4 + 8,
                                         tower.level)

            if (hasattr(tower, 'tower_hp')
                    and tower.tower_hp < tower.tower_max_hp):
                bar_w = self.tile_size // 2
                bar_h = 3
                bar_x = cx - bar_w // 2
                bar_y = cy + self.tile_size // 4 + 20
                self._draw_health_bar(bar_x, bar_y, bar_w, bar_h,
                                      tower.get_tower_hp_ratio())

            if (tower.target and tower.target.is_alive
                    and tower.attack_cooldown
                    > tower.attack_speed * 0.85):
                flash_colors = {
                    TowerType.ARCHER: (255, 220, 120),
                    TowerType.MAGE: (200, 140, 255),
                    TowerType.ARTILLERY: (255, 180, 60),
                    TowerType.FREEZE: (160, 220, 255),
                    TowerType.POISON: (120, 240, 80),
                    TowerType.TESLA: (140, 200, 255),
                    TowerType.LASER: (255, 120, 120),
                    TowerType.BALLISTA: (240, 220, 140),
                    TowerType.NECROMANCER: (100, 255, 100),
                }
                fc = flash_colors.get(tower.tower_type, (255, 255, 200))
                glow_c = tuple(min(255, c + 60) for c in fc)
                pygame.draw.circle(self.screen, fc, (cx, cy - 6), 10, 3)
                pygame.draw.circle(self.screen, glow_c, (cx, cy - 6), 5)
                pygame.draw.circle(self.screen, (255, 255, 255),
                                   (cx, cy - 6), 2)

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
    # Projectiles (sprite blit + rotation)
    # ------------------------------------------------------------------

    def _draw_projectiles(self, projectiles):
        """Draw projectiles with trail lines and sprite-based heads."""
        _PROJ_COLORS = {
            TowerType.ARCHER: ((220, 180, 80), (255, 230, 150)),
            TowerType.MAGE: ((180, 80, 255), (230, 180, 255)),
            TowerType.NECROMANCER: ((60, 220, 60), (150, 255, 150)),
            TowerType.POISON: ((80, 200, 40), (160, 240, 120)),
            TowerType.FREEZE: ((100, 200, 255), (200, 240, 255)),
            TowerType.ARTILLERY: ((255, 160, 40), (255, 220, 120)),
            TowerType.BALLISTA: ((200, 180, 100), (240, 230, 180)),
            TowerType.FORTRESS: ((160, 160, 170), (210, 210, 220)),
        }
        _PHYSICAL = {TowerType.ARCHER, TowerType.ARTILLERY,
                     TowerType.BALLISTA, TowerType.FORTRESS}
        _MAGIC = {TowerType.MAGE, TowerType.NECROMANCER, TowerType.POISON}

        for proj in projectiles:
            px, py = int(proj["x"]), int(proj["y"])
            tt = proj["tower_type"]
            dx = proj["target_x"] - proj["x"]
            dy = proj["target_y"] - proj["y"]
            dist = max(1.0, math.sqrt(dx * dx + dy * dy))
            nx, ny = dx / dist, dy / dist
            color, glow = _PROJ_COLORS.get(
                tt, ((220, 200, 100), (255, 240, 180)))

            trail_len = 28
            mid_len = 18
            tail = (int(px - nx * trail_len), int(py - ny * trail_len))
            mid = (int(px - nx * mid_len), int(py - ny * mid_len))
            pygame.draw.line(self.screen, color, tail, (px, py), 4)
            pygame.draw.line(self.screen, glow, mid, (px, py), 2)

            if tt == TowerType.ARTILLERY:
                pygame.draw.circle(self.screen, color, (px, py), 8)
                pygame.draw.circle(self.screen, glow, (px, py), 5)
                pygame.draw.circle(self.screen, (255, 255, 255),
                                   (px, py), 2)
            elif tt in _PHYSICAL:
                tip = (int(px + nx * 6), int(py + ny * 6))
                left = (int(px - nx * 4 - ny * 3),
                        int(py - ny * 4 + nx * 3))
                right = (int(px - nx * 4 + ny * 3),
                         int(py - ny * 4 - nx * 3))
                pygame.draw.polygon(self.screen, color,
                                    [tip, left, right])
                pygame.draw.circle(self.screen, glow, (px, py), 3)
            elif tt in _MAGIC:
                pygame.draw.circle(self.screen, glow, (px, py), 7)
                pygame.draw.circle(self.screen, color, (px, py), 5)
                for si in range(4):
                    sa = self.anim_tick * 0.3 + si * math.pi / 2
                    spx = int(px + math.cos(sa) * 8)
                    spy = int(py + math.sin(sa) * 8)
                    pygame.draw.circle(self.screen, glow,
                                       (spx, spy), 2)
            elif tt == TowerType.FREEZE:
                pygame.draw.circle(self.screen, glow, (px, py), 6)
                pygame.draw.circle(self.screen, (255, 255, 255),
                                   (px, py), 3)
            else:
                pygame.draw.circle(self.screen, color, (px, py), 6)
                pygame.draw.circle(self.screen, glow, (px, py), 3)

    def _draw_attack_beams(self, towers):
        """Draw beam/lightning for Tesla/Laser and targeting lines for all.

        Every tower with a living target gets a faint colored targeting
        line so the player can see who is shooting whom.
        """
        _LINE_COLORS = {
            TowerType.ARCHER: (180, 150, 60),
            TowerType.MAGE: (140, 60, 200),
            TowerType.ARTILLERY: (200, 120, 30),
            TowerType.FREEZE: (80, 160, 220),
            TowerType.POISON: (60, 160, 40),
            TowerType.NECROMANCER: (50, 180, 50),
            TowerType.BALLISTA: (160, 140, 80),
            TowerType.FORTRESS: (130, 130, 140),
        }

        for tower in towers:
            if tower.target is None or not tower.target.is_alive:
                continue

            cx, cy = tower.pixel_x, tower.pixel_y
            tx, ty = int(tower.target.x), int(tower.target.y)
            firing = tower.attack_cooldown > tower.attack_speed * 0.7

            if tower.tower_type == TowerType.TESLA and not firing:
                points = [(cx, cy - 6)]
                ddx, ddy = tx - cx, ty - (cy - 6)
                segments = 10
                for i in range(1, segments):
                    frac = i / segments
                    mx = cx + ddx * frac + random.randint(-14, 14)
                    my = (cy - 6) + ddy * frac + random.randint(-14, 14)
                    points.append((int(mx), int(my)))
                points.append((tx, ty))
                pygame.draw.lines(self.screen, (60, 110, 230),
                                  False, points, 4)
                pygame.draw.lines(self.screen, (160, 200, 255),
                                  False, points, 2)
                pygame.draw.lines(self.screen, (220, 240, 255),
                                  False, points, 1)
                pygame.draw.circle(self.screen, (200, 230, 255),
                                   (tx, ty), 10, 3)
                pygame.draw.circle(self.screen, (255, 255, 255),
                                   (tx, ty), 4)

            elif tower.tower_type == TowerType.LASER and not firing:
                pygame.draw.line(self.screen, (180, 20, 20),
                                 (cx, cy), (tx, ty), 7)
                pygame.draw.line(self.screen, (255, 80, 80),
                                 (cx, cy), (tx, ty), 4)
                pygame.draw.line(self.screen, (255, 180, 180),
                                 (cx, cy), (tx, ty), 2)
                pygame.draw.line(self.screen, (255, 240, 240),
                                 (cx, cy), (tx, ty), 1)
                pygame.draw.circle(self.screen, (255, 100, 50),
                                   (tx, ty), 10)
                pygame.draw.circle(self.screen, (255, 200, 100),
                                   (tx, ty), 5)

            elif tower.tower_type not in (TowerType.BARRACKS,
                                          TowerType.TESLA,
                                          TowerType.LASER):
                line_c = _LINE_COLORS.get(tower.tower_type, (150, 150, 100))
                pygame.draw.line(self.screen, line_c,
                                 (cx, cy), (tx, ty), 1)

    # ------------------------------------------------------------------
    # Enemies (generic sprite blit)
    # ------------------------------------------------------------------

    def _draw_enemies(self, enemies):
        """Draw all living enemies using sprites with direction flipping."""
        from enums import EnemyType
        for enemy in enemies:
            if not enemy.is_alive:
                continue
            cx, cy = int(enemy.x), int(enemy.y)
            sprite = self.assets.enemies.get(enemy.enemy_type)
            if sprite is None:
                continue

            is_boss = enemy.enemy_type == EnemyType.BOSS
            bob = int(math.sin(self.anim_tick * 0.15) * 2)
            w, h = sprite.get_size()

            img = sprite
            if hasattr(enemy, 'direction_x') and enemy.direction_x > 0:
                img = pygame.transform.flip(img, True, False)
                img.set_colorkey((255, 0, 255))

            if enemy.hit_timer > 0:
                hit_surf = img.copy()
                hit_surf.fill((200, 80, 80),
                              special_flags=pygame.BLEND_RGB_ADD)
                hit_surf.set_colorkey((255, 0, 255))
                img = hit_surf

            self.screen.blit(img, (cx - w // 2, cy - h // 2 + bob))

            if is_boss:
                self._draw_boss_indicator(cx, cy, w, h, enemy)
            else:
                self._draw_health_bar(cx - 14, cy - 22, 28, 4,
                                      enemy.get_hp_ratio())

            if hasattr(enemy, 'slow_timer') and enemy.slow_timer > 0:
                r = 16 if is_boss else 11
                pygame.draw.circle(self.screen, (100, 180, 255),
                                   (cx, cy), r, 1)

            if hasattr(enemy, 'poison_timer') and enemy.poison_timer > 0:
                dist = 18 if is_boss else 12
                for pi in range(3):
                    pa = self.anim_tick * 0.15 + pi * 2.1
                    ppx = int(cx + math.cos(pa) * dist)
                    ppy = int(cy + math.sin(pa) * dist)
                    pygame.draw.circle(self.screen, (100, 220, 50),
                                       (ppx, ppy), 2)

    def _draw_boss_indicator(self, cx, cy, w, h, enemy):
        """Draw boss-specific UI: larger HP bar, name tag, crown icon.

        Args:
            cx: Center X pixel of boss.
            cy: Center Y pixel of boss.
            w: Sprite width.
            h: Sprite height.
            enemy: Enemy instance.
        """
        bar_w = max(40, w + 10)
        bar_h = 6
        bar_x = cx - bar_w // 2
        bar_y = cy - h // 2 - 16
        self._draw_health_bar(bar_x, bar_y, bar_w, bar_h,
                              enemy.get_hp_ratio())

        crown_y = bar_y - 10
        pts = [
            (cx - 8, crown_y + 6), (cx - 8, crown_y),
            (cx - 4, crown_y + 3), (cx, crown_y - 2),
            (cx + 4, crown_y + 3), (cx + 8, crown_y),
            (cx + 8, crown_y + 6),
        ]
        pygame.draw.polygon(self.screen, (255, 200, 40), pts)
        pygame.draw.polygon(self.screen, (200, 150, 20), pts, 1)

    # ------------------------------------------------------------------
    # Soldiers (sprite blit)
    # ------------------------------------------------------------------

    def _draw_soldiers(self, soldiers):
        """Draw all living soldiers using sprites."""
        for soldier in soldiers:
            if not soldier.is_alive:
                continue
            cx, cy = int(soldier.x), int(soldier.y)
            self._draw_shadow(cx, cy + 6, 7)

            if soldier.target:
                sprite = self.assets.soldiers.get("fight",
                                                   self.assets.soldiers["idle"])
            else:
                sprite = self.assets.soldiers["idle"]

            bob = int(math.sin(self.anim_tick * 0.2) * 1) if soldier.target else 0
            w, h = sprite.get_size()
            self.screen.blit(sprite, (cx - w // 2, cy - h // 2 + bob))

            self._draw_health_bar(cx - 8, cy - 17, 16, 3,
                                  soldier.get_hp_ratio())

    # ------------------------------------------------------------------
    # Health bars
    # ------------------------------------------------------------------

    def _draw_health_bar(self, x, y, width, height, ratio):
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
        """Draw a subtle attack range ring for a selected tower."""
        cx, cy = tower.pixel_x, tower.pixel_y
        range_pixels = int(tower.attack_range * self.tile_size)
        pygame.draw.circle(self.screen, (255, 255, 200),
                           (cx, cy), range_pixels, 2)
        pygame.draw.circle(self.screen, (200, 200, 180),
                           (cx, cy), range_pixels - 1, 1)
