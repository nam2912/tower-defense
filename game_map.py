"""Game map module.

Manages the tile grid, enemy path waypoints, and valid tower build spots.

Design patterns: Tile-Based Map.
See REFERENCES.md for full citations.
"""

import math


class GameMap:
    """Represents the game map with grid, path, and build spots.

    Attributes:
        tile_size: Size of each tile in pixels.
        cols: Number of columns in the grid.
        rows: Number of rows in the grid.
        path_waypoints: List of (x, y) tuples defining the enemy path.
        build_spots: List of (col, row) tuples where towers can be placed.
        grid: 2D list representing tile types.
    """

    def __init__(self, config):
        """Initialize the game map from configuration.

        Args:
            config: Game configuration dictionary.
        """
        pass

    def _init_default_map(self):
        """Set up the default map layout with path and build spots."""
        pass

    def _mark_path_on_grid(self):
        """Mark path tiles on the grid based on waypoints."""
        pass

    def _mark_line(self, start, end):
        """Mark a straight line between two waypoints on the grid.

        Args:
            start: Starting (col, row) tuple.
            end: Ending (col, row) tuple.
        """
        pass

    def _generate_build_spots(self):
        """Generate valid build spots adjacent to the path."""
        pass

    def is_build_spot(self, col, row):
        """Check if a grid position is a valid build spot.

        Args:
            col: Column index.
            row: Row index.

        Returns:
            True if the position is a valid build spot.
        """
        pass

    def is_path_tile(self, col, row):
        """Check if a grid position is part of the enemy path.

        Args:
            col: Column index.
            row: Row index.

        Returns:
            True if the position is a path tile.
        """
        pass

    def get_pixel_pos(self, col, row):
        """Convert grid coordinates to pixel coordinates (center of tile).

        Args:
            col: Column index.
            row: Row index.

        Returns:
            Tuple (x, y) pixel position at center of the tile.
        """
        pass

    def get_grid_pos(self, pixel_x, pixel_y):
        """Convert pixel coordinates to grid coordinates.

        Args:
            pixel_x: X pixel position.
            pixel_y: Y pixel position.

        Returns:
            Tuple (col, row) grid position.
        """
        pass

    def get_path_pixel_waypoints(self):
        """Get path waypoints in pixel coordinates.

        Returns:
            List of (x, y) tuples in pixel coordinates.
        """
        pass

    def remove_build_spot(self, col, row):
        """Remove a build spot after a tower is placed.

        Args:
            col: Column index.
            row: Row index.
        """
        pass

    def add_build_spot(self, col, row):
        """Re-add a build spot when a tower is sold.

        Args:
            col: Column index.
            row: Row index.
        """
        pass
