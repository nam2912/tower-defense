"""Asset loader module.

Loads and caches all sprite assets once at startup. Sprites are read from
the ``assets/`` directory and scaled to the configured tile size so that
the renderer only needs to ``blit()`` pre-scaled surfaces.

Asset sources (all CC0):
- Kenney Tower Defense (top-down) — https://opengameart.org/content/tower-defense-300-tilessprites
- Kenney Particle Pack — https://opengameart.org/content/particle-pack-80-sprites
- Kenney UI Pack — https://opengameart.org/content/ui-pack
"""

import os
import random
import pygame
from enums import TowerType, EnemyType


class AssetLoader:
    """Load and cache all sprite assets once at startup.

    Attributes:
        tile_size: Target tile dimension in pixels.
        terrain: Dict of terrain sprite surfaces.
        towers: Dict mapping TowerType to a sprite surface.
        enemies: Dict mapping EnemyType to a sprite surface.
        soldiers: Dict with 'idle' and 'fight' soldier sprites.
        ui: Dict of UI element sprite surfaces.
        font: Loaded Kenney Future font, or fallback system font.
    """

    def __init__(self, assets_dir, tile_size):
        """Initialize the asset loader and load all sprites.

        Args:
            assets_dir: Absolute path to the assets directory.
            tile_size: Target tile dimension in pixels.
        """
        self.tile_size = tile_size
        self._dir = assets_dir
        self.terrain = {}
        self.towers = {}
        self.enemies = {}
        self.soldiers = {}
        self.ui = {}
        self.font = None
        self._load_all()

    def _load(self, *path_parts, size=None, alpha=True):
        """Load a single image from disk and optionally scale it.

        Kenney sprites have white (255,255,255) pixels with alpha=0 in
        transparent areas. On some display backends (notably macOS retina),
        ``convert_alpha()`` fails to preserve per-pixel alpha correctly.
        This method works around the issue by using ``set_colorkey`` to
        mark pure white as transparent before compositing onto a clean
        SRCALPHA surface.

        Args:
            *path_parts: Path components relative to the assets directory.
            size: Optional (width, height) tuple to scale to.
            alpha: Whether to use per-pixel alpha (convert_alpha).

        Returns:
            Loaded pygame Surface, or a magenta placeholder on error.
        """
        full_path = os.path.join(self._dir, *path_parts)
        if not os.path.exists(full_path):
            placeholder = pygame.Surface(
                (self.tile_size, self.tile_size))
            placeholder.fill((255, 0, 255))
            placeholder.set_colorkey((255, 0, 255))
            return placeholder
        raw = pygame.image.load(full_path).convert_alpha()
        if size is not None:
            raw = pygame.transform.scale(raw, size)
        w, h = raw.get_size()
        result = pygame.Surface((w, h))
        result.fill((255, 0, 255))
        result.blit(raw, (0, 0))
        result.set_colorkey((255, 0, 255))
        return result

    def _ts(self, factor=1.0):
        """Return a (width, height) tuple based on tile_size and a factor."""
        s = int(self.tile_size * factor)
        return (s, s)

    def _load_all(self):
        """Load every category of sprite assets."""
        self._load_terrain()
        self._load_towers()
        self._load_enemies()
        self._load_soldiers()
        self._load_ui()
        self._load_font()

    def _load_terrain(self):
        """Load terrain tile sprites (grass, path variants, platforms, decorations)."""
        ts = self._ts()
        self.terrain["grass"] = self._load("terrain", "grass.png", size=ts)

        path_names = [
            "path_center", "path_corner_tl", "path_corner_tr",
            "path_corner_bl", "path_corner_br",
            "path_straight_h", "path_straight_v",
            "path_t_top", "path_t_left",
            "path_cross",
            "path_end_top", "path_end_right",
            "path_end_bottom", "path_end_left",
        ]
        for name in path_names:
            self.terrain[name] = self._load("terrain", f"{name}.png", size=ts)

        self.terrain["platform"] = self._load("terrain", "platform.png",
                                              size=ts)
        self.terrain["platform_locked"] = self._load("terrain",
                                                     "platform_locked.png",
                                                     size=ts)

        deco_names = ["rock1", "rock2", "rock3", "tree_round", "bush",
                      "star_bush", "mountain", "rock_cluster"]
        deco_size = self._ts(0.85)
        for name in deco_names:
            self.terrain[name] = self._load("terrain", f"{name}.png",
                                           size=deco_size)

    def _load_towers(self):
        """Load tower sprites keyed by TowerType."""
        ts = self._ts(0.85)
        tower_files = {
            TowerType.FORTRESS: "tower_fortress.png",
            TowerType.ARCHER: "tower_archer.png",
            TowerType.BARRACKS: "tower_barracks.png",
            TowerType.MAGE: "tower_mage.png",
            TowerType.ARTILLERY: "tower_artillery.png",
            TowerType.FREEZE: "tower_freeze.png",
            TowerType.POISON: "tower_poison.png",
            TowerType.BALLISTA: "tower_ballista.png",
            TowerType.TESLA: "tower_tesla.png",
            TowerType.NECROMANCER: "tower_necromancer.png",
            TowerType.LASER: "tower_laser.png",
        }
        for t_type, filename in tower_files.items():
            self.towers[t_type] = self._load("towers", filename, size=ts)

        self.tower_base_main = self._load("towers", "tower_base.png",
                                          size=self._ts(0.95))

    def _load_enemies(self):
        """Load enemy sprites keyed by EnemyType."""
        sizes = {
            EnemyType.GRUNT: self._ts(0.6),
            EnemyType.RUNNER: self._ts(0.55),
            EnemyType.ARMORED: self._ts(0.7),
            EnemyType.BOMBER: self._ts(0.65),
            EnemyType.BOSS: self._ts(1.35),
        }
        enemy_files = {
            EnemyType.GRUNT: "enemy_grunt.png",
            EnemyType.RUNNER: "enemy_runner.png",
            EnemyType.ARMORED: "enemy_armored.png",
            EnemyType.BOMBER: "enemy_bomber.png",
            EnemyType.BOSS: "enemy_boss.png",
        }
        for e_type, filename in enemy_files.items():
            self.enemies[e_type] = self._load("enemies", filename,
                                              size=sizes[e_type])

    def _load_soldiers(self):
        """Load soldier sprites for idle and fighting states."""
        s = self._ts(0.35)
        self.soldiers["idle"] = self._load("soldiers", "soldier.png", size=s)
        self.soldiers["fight"] = self._load("soldiers", "soldier_fight.png",
                                            size=s)

    def _load_ui(self):
        """Load UI sprites (buttons, icons, panels)."""
        btn_size = (120, 48)
        icon_size = (32, 32)
        self.ui["btn_green"] = self._load("ui", "btn_green.png", size=btn_size)
        self.ui["btn_red"] = self._load("ui", "btn_red.png", size=btn_size)
        self.ui["btn_yellow"] = self._load("ui", "btn_yellow.png",
                                           size=btn_size)
        self.ui["btn_blue"] = self._load("ui", "btn_blue.png", size=btn_size)
        self.ui["btn_grey"] = self._load("ui", "btn_grey.png", size=btn_size)
        self.ui["btn_square_grey"] = self._load("ui", "btn_square_grey.png",
                                                size=(48, 48))
        self.ui["btn_square_green"] = self._load("ui", "btn_square_green.png",
                                                 size=(48, 48))
        self.ui["icon_upgrade"] = self._load("ui", "icon_upgrade.png",
                                             size=icon_size)
        self.ui["icon_sell"] = self._load("ui", "icon_sell.png",
                                          size=icon_size)
        self.ui["panel_bg"] = self._load("ui", "panel_bg.png",
                                         size=(200, 100))
        self.ui["castle"] = self._load("ui", "castle.png",
                                       size=self._ts(1.2))

    def _load_font(self):
        """Load the bundled Kenney Future font, falling back to system Arial."""
        font_path = os.path.join(self._dir, "ui", "Kenney Future.ttf")
        if os.path.exists(font_path):
            self.font_path = font_path
        else:
            self.font_path = None

    def get_font(self, size, bold=False):
        """Return a pygame Font at the requested size.

        Args:
            size: Font point size.
            bold: Whether to use bold rendering.

        Returns:
            A pygame.font.Font instance.
        """
        if self.font_path is not None:
            return pygame.font.Font(self.font_path, size)
        return pygame.font.SysFont("Arial", size, bold=bold)

    def get_tower_icon(self, tower_type, size=None):
        """Return a scaled tower sprite suitable for an icon.

        Args:
            tower_type: Which tower to get the icon for.
            size: Optional (w, h) override.

        Returns:
            Scaled pygame Surface.
        """
        base = self.towers.get(tower_type)
        if base is None:
            s = pygame.Surface((24, 24))
            s.fill((255, 0, 255))
            s.set_colorkey((255, 0, 255))
            return s
        if size is not None:
            return pygame.transform.scale(base, size)
        return base

    def get_decoration(self, col, row):
        """Return a deterministic decoration sprite for a non-buildable tile.

        Every non-buildable grass tile receives a decoration so empty
        tiles are visually distinct from build platforms.

        Args:
            col: Grid column.
            row: Grid row.

        Returns:
            A decoration Surface (always non-None).
        """
        rng = random.Random(col * 7919 + row * 6271)
        keys = ["rock1", "rock2", "rock3", "tree_round", "bush",
                "star_bush", "mountain", "rock_cluster"]
        return self.terrain[keys[rng.randint(0, len(keys) - 1)]]
