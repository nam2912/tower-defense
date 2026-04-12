"""Procedural particle-based impact effects for tower attacks.

Renders expanding flash, shockwave ring, and scatter particles at
projectile impact points using ``pygame.draw`` primitives only.
No sprite blitting — avoids colorkey/alpha artifacts on rotated or
scaled surfaces (black corners, magenta bleeding on macOS retina).
"""

import math
import random

import pygame


class Effects:
    """Spawns and animates impact particle effects."""

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
            kind: Effect type key in ``_COLORS``.
            size: Approximate diameter of the effect.
        """
        primary, secondary, flash = self._COLORS.get(
            kind, self._COLORS["explosion"])

        rng = random.Random()
        particles = []
        count = max(10, size // 4)
        for _ in range(count):
            angle = rng.uniform(0, math.tau)
            speed = rng.uniform(2.0, 5.5)
            r = rng.randint(3, max(4, size // 8))
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
            "lifetime": 0.45,
        })

    def update(self, dt):
        """Advance all active effects and remove expired ones."""
        alive = []
        for fx in self.active:
            fx["age"] += dt
            if fx["age"] < fx["lifetime"]:
                for p in fx["particles"]:
                    p["dx"] *= 0.92
                    p["dy"] *= 0.92
                alive.append(fx)
        self.active = alive

    def draw(self, screen, assets=None):
        """Draw all active effects using procedural primitives.

        Args:
            screen: Target pygame surface.
            assets: Ignored (kept for API compatibility).
        """
        for fx in self.active:
            x, y = int(fx["x"]), int(fx["y"])
            progress = fx["age"] / fx["lifetime"]
            fade = max(0.0, 1.0 - progress)

            if progress < 0.3:
                flash_t = progress / 0.3
                flash_r = int(fx["max_radius"] * (1.0 - flash_t) * 1.2)
                if flash_r > 2:
                    pygame.draw.circle(screen, fx["flash"],
                                       (x, y), flash_r)
                    inner_r = max(1, flash_r // 2)
                    pygame.draw.circle(screen, (255, 255, 255),
                                       (x, y), inner_r)

            ring_r = int(fx["max_radius"] * 1.3 * progress)
            if ring_r > 3:
                thickness = max(1, int(4 * fade))
                pygame.draw.circle(screen, fx["primary"],
                                   (x, y), ring_r, thickness)

            for p in fx["particles"]:
                px = int(x + p["dx"] * fx["age"] * 65)
                py = int(y + p["dy"] * fx["age"] * 65)
                pr = max(1, int(p["r"] * fade))
                if pr > 0:
                    pygame.draw.circle(screen, p["color"], (px, py), pr)
                    if pr > 2:
                        bright = tuple(min(255, c + 80) for c in p["color"])
                        pygame.draw.circle(screen, bright,
                                           (px, py), max(1, pr // 2))
