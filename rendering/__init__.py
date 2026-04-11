"""Rendering package — splits the Renderer class into logical mixins.

The ``Renderer`` class lives in ``renderer.py`` (the project root) and
inherits from the three mixin classes defined in this package:

* ``RendererEntitiesMixin``  — towers, enemies, soldiers, projectiles
* ``RendererHudMixin``       — HUD, tower bar, radial menus, debug
* ``RendererOverlaysMixin``  — menu, pause, round screens, button rects
"""

from rendering.draw_entities import RendererEntitiesMixin
from rendering.draw_hud import RendererHudMixin
from rendering.draw_overlays import RendererOverlaysMixin

__all__ = [
    "RendererEntitiesMixin",
    "RendererHudMixin",
    "RendererOverlaysMixin",
]
