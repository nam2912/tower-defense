"""Renderer module.

Draws sprites, health bars, projectiles, and UI overlay using Pygame.
All drawing functions receive the surface and data as parameters —
no global state.

Design patterns: Separation of Concerns (Model-View).
See REFERENCES.md for full citations.
"""

import pygame
from enums import TowerType, GameState


class Renderer:
    """Handles all game rendering and UI drawing.

    Attributes:
        screen: Pygame display surface.
        config: Game configuration dictionary.
        tile_size: Tile size in pixels.
        font_small: Small font for labels.
        font_medium: Medium font for UI.
        font_large: Large font for titles.
    """

    def __init__(self, screen, config):
        """Initialize the renderer.

        Args:
            screen: Pygame display surface.
            config: Game configuration dictionary.
        """
        pass

    def draw_game(self, game_map, towers, enemies, soldiers,
                  gold, lives, wave_info, selected_tower_type,
                  hover_pos, selected_tower):
        """Draw the complete game frame.

        Args:
            game_map: GameMap instance.
            towers: List of Tower instances.
            enemies: List of Enemy instances.
            soldiers: List of Soldier instances.
            gold: Current player gold.
            lives: Current player lives.
            wave_info: Tuple (current_wave, total_waves).
            selected_tower_type: TowerType being placed, or None.
            hover_pos: Tuple (col, row) of mouse hover position.
            selected_tower: Tower instance selected for info, or None.
        """
        pass

    def _draw_map(self, game_map, colors):
        """Draw the tile grid and path.

        Args:
            game_map: GameMap instance.
            colors: Color configuration dictionary.
        """
        pass

    def _draw_build_spots(self, game_map, colors, hover_pos, selected_tower_type):
        """Draw valid build spots with hover highlight.

        Args:
            game_map: GameMap instance.
            colors: Color configuration dictionary.
            hover_pos: Tuple (col, row) or None.
            selected_tower_type: TowerType being placed, or None.
        """
        pass

    def _draw_towers(self, towers, colors):
        """Draw all towers on the map.

        Args:
            towers: List of Tower instances.
            colors: Color configuration dictionary.
        """
        pass

    def _draw_enemies(self, enemies, colors):
        """Draw all living enemies with health bars.

        Args:
            enemies: List of Enemy instances.
            colors: Color configuration dictionary.
        """
        pass

    def _draw_soldiers(self, soldiers, colors):
        """Draw all living soldiers with health bars.

        Args:
            soldiers: List of Soldier instances.
            colors: Color configuration dictionary.
        """
        pass

    def _draw_health_bar(self, x, y, width, height, ratio, colors):
        """Draw a health bar at the specified position.

        Args:
            x: Left edge x position.
            y: Top edge y position.
            width: Total bar width.
            height: Bar height.
            ratio: HP ratio (0.0 to 1.0).
            colors: Color configuration dictionary.
        """
        pass

    def _draw_tower_range(self, tower):
        """Draw the attack range circle for a selected tower.

        Args:
            tower: Tower instance.
        """
        pass

    def _draw_ui_panel(self, gold, lives, wave_info, selected_tower_type,
                       selected_tower, colors):
        """Draw the bottom UI panel with game info and tower shop.

        Args:
            gold: Current player gold.
            lives: Current player lives.
            wave_info: Tuple (current_wave, total_waves).
            selected_tower_type: TowerType being placed, or None.
            selected_tower: Tower selected for info, or None.
            colors: Color configuration dictionary.
        """
        pass

    def _draw_tower_buttons(self, panel_top, colors, selected_tower_type):
        """Draw tower purchase buttons in the UI panel.

        Args:
            panel_top: Y position of the panel top edge.
            colors: Color configuration dictionary.
            selected_tower_type: Currently selected TowerType, or None.
        """
        pass

    def draw_menu(self):
        """Draw the main menu screen."""
        pass

    def draw_game_over(self, wave_info):
        """Draw the game over screen.

        Args:
            wave_info: Tuple (current_wave, total_waves).
        """
        pass

    def draw_pause_overlay(self):
        """Draw a semi-transparent pause overlay."""
        pass

    def draw_victory(self):
        """Draw the victory screen."""
        pass

    def get_tower_button_rects(self):
        """Get clickable rectangles for tower purchase buttons.

        Returns:
            List of (TowerType, pygame.Rect) tuples.
        """
        pass
