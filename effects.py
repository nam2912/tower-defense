"""Procedural particle-based impact effects for tower attacks.

Draws expanding rings and scatter particles directly onto the screen
surface, avoiding sprite sheets and alpha-blending issues on macOS.
"""

import math
import random

import pygame


class Effects:
    """Spawns and animates procedural particle effects at impact points."""

    _COLORS = {
        "explosion": ((255, 160, 40), (255, 80, 20), (255, 220, 80)),
        "impact": ((200, 200, 220), (160, 160, 180), (255, 255, 255)),
        "aura": ((100, 200, 255), (60, 140, 220), (200, 240, 255)),
    }

    def __init__(self):
        """Initialize the effects manager."""
        self.active = []

    def spawn(self, x, y, kind="explosion", size=64):
        """Spawn an effect at (x, y).

        Args:
            x: Center X pixel position.
            y: Center Y pixel position.
            kind: Effect type — "explosion", "impact", or "aura".
            size: Approximate radius of the effect.
        """
        primary, secondary, flash = self._COLORS.get(
            kind, self._COLORS["explosion"])

        rng = random.Random()
        particles = []
        count = max(8, size // 5)
        for _ in range(count):
            angle = rng.uniform(0, math.tau)
            speed = rng.uniform(1.5, 4.0)
            r = rng.randint(2, max(3, size // 12))
            c = primary if rng.random() > 0.4 else secondary
            particles.append({
                "dx": math.cos(angle) * speed,
                "dy": math.sin(angle) * speed,
                "r": r,
                "color": c,
            })

        self.active.append({
            "x": x, "y": y,
            "particles": particles,
            "max_radius": size // 2,
            "flash": flash,
            "primary": primary,
            "age": 0.0,
            "lifetime": 0.4,
        })

    def update(self, dt):
        """Advance all active effects and remove expired ones."""
        alive = []
        for fx in self.active:
            fx["age"] += dt
            if fx["age"] < fx["lifetime"]:
                for p in fx["particles"]:
                    p["dx"] *= 0.93
                    p["dy"] *= 0.93
                alive.append(fx)
        self.active = alive

    def draw(self, screen, assets=None):
        """Draw all active effects using particle sprites when available."""
        for fx in self.active:
            x, y = fx["x"], fx["y"]
            progress = fx["age"] / fx["lifetime"]

            if progress < 0.25 and assets is not None:
                flash_r = int(fx["max_radius"] * (1.0 - progress / 0.25))
                if flash_r > 2:
                    sprite = assets.particles.get("flare")
                    if sprite is not None:
                        size = flash_r * 2
                        scaled = pygame.transform.scale(sprite, (size, size))
                        scaled.set_colorkey((255, 0, 255))
                        screen.blit(scaled, (x - size // 2, y - size // 2))
                    else:
                        pygame.draw.circle(screen, fx["flash"], (x, y), flash_r)
            elif progress < 0.25:
                flash_r = int(fx["max_radius"] * (1.0 - progress / 0.25))
                if flash_r > 2:
                    pygame.draw.circle(screen, fx["flash"], (x, y), flash_r)

            ring_r = int(fx["max_radius"] * progress)
            if ring_r > 3:
                thickness = max(1, int(3 * (1.0 - progress)))
                pygame.draw.circle(screen, fx["primary"],
                                   (x, y), ring_r, thickness)

            for p in fx["particles"]:
                px = int(x + p["dx"] * fx["age"] * 60)
                py = int(y + p["dy"] * fx["age"] * 60)
                pr = max(1, int(p["r"] * (1.0 - progress)))
                if pr > 0 and assets is not None:
                    sprite = assets.particles.get("fire")
                    if sprite is not None:
                        size = pr * 3
                        scaled = pygame.transform.scale(sprite, (size, size))
                        scaled.set_colorkey((255, 0, 255))
                        screen.blit(scaled, (px - size // 2, py - size // 2))
                    else:
                        pygame.draw.circle(screen, p["color"], (px, py), pr)
                elif pr > 0:
                    pygame.draw.circle(screen, p["color"], (px, py), pr)
