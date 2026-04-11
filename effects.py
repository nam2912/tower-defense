"""Sprite-based impact effects for tower attacks.

Loads sprite sheets from assets/ and plays them at impact locations.

Assets from OpenGameArt.org (CC0 — free, no credit needed):
- explosion.png by Soluna Software
- impact.png by Soluna Software
- aura.png by Soluna Software
"""

import os
import pygame


class Effects:
    """Loads sprite sheets once, spawns and plays animations at impact points."""

    def __init__(self):
        """Load all sprite sheets into frame lists."""
        self.assets_dir = os.path.join(os.path.dirname(__file__), "assets")
        self.explosion_frames = self._load_frames("explosion.png", 4, 4)
        self.impact_frames = self._load_frames("impact.png", 4, 4)
        self.aura_frames = self._load_frames("aura.png", 4, 4)
        self.active = []

    def _load_frames(self, filename, cols, rows):
        """Load a sprite sheet and slice it into a list of frames.

        Args:
            filename: Image file in the assets folder.
            cols: Number of columns in the grid.
            rows: Number of rows in the grid.

        Returns:
            List of pygame Surfaces, or empty list if file not found.
        """
        path = os.path.join(self.assets_dir, filename)
        if not os.path.exists(path):
            return []
        sheet = pygame.image.load(path).convert_alpha()
        w = sheet.get_width() // cols
        h = sheet.get_height() // rows
        frames = []
        for row in range(rows):
            for col in range(cols):
                frame = sheet.subsurface((col * w, row * h, w, h))
                frames.append(frame)
        return frames

    def spawn(self, x, y, kind="explosion", size=64):
        """Spawn an animation at (x, y).

        Args:
            x: Center X pixel position.
            y: Center Y pixel position.
            kind: Which animation — "explosion", "impact", or "aura".
            size: Width/height to scale each frame to.
        """
        frames_map = {
            "explosion": self.explosion_frames,
            "impact": self.impact_frames,
            "aura": self.aura_frames,
        }
        frames = frames_map.get(kind, self.explosion_frames)
        if not frames:
            return
        self.active.append({
            "x": x, "y": y,
            "frames": frames,
            "frame_index": 0,
            "size": size,
            "timer": 0.0,
            "speed": 0.04,
        })

    def update(self, dt):
        """Advance all active animations. Remove finished ones."""
        alive = []
        for anim in self.active:
            anim["timer"] += dt
            if anim["timer"] >= anim["speed"]:
                anim["timer"] = 0.0
                anim["frame_index"] += 1
            if anim["frame_index"] < len(anim["frames"]):
                alive.append(anim)
        self.active = alive

    def draw(self, screen):
        """Draw current frame of each active animation."""
        for anim in self.active:
            frame = anim["frames"][anim["frame_index"]]
            scaled = pygame.transform.scale(frame, (anim["size"], anim["size"]))
            screen.blit(scaled, (anim["x"] - anim["size"] // 2,
                                 anim["y"] - anim["size"] // 2))
