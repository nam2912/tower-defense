"""Game map module.

Tile grid, enemy path waypoints, and tower build slots. Some slots are free
from the start; locked ones need gold before you can build there.
"""

import random


class GameMap:
    """Represents the game map with grid, path, and build spots.

    Attributes:
        tile_size: Size of each tile in pixels.
        cols: Number of columns in the grid.
        rows: Number of rows in the grid.
        path_waypoints: List of (x, y) tuples defining the enemy path.
        build_spots: List of (col, row) tuples where towers can be placed.
        locked_spots: List of (col, row) tuples requiring gold to unlock.
        grid: 2D list representing tile types.
    """

    def __init__(self, config):
        """Initialize the game map from configuration.

        Args:
            config: Game configuration dictionary.
        """
        grid_config = config["grid"]
        self.tile_size = grid_config["tile_size"]
        self.cols = grid_config["cols"]
        self.rows = grid_config["rows"]
        self.path_waypoints = []
        self.build_spots = []
        self.locked_spots = []
        self.grid = []
        free_count = config["gameplay"].get("free_build_slots", 999)
        self._init_default_map(free_count)

    def _init_default_map(self, free_count):
        """Set up the default map layout with path and build spots.

        Args:
            free_count: Number of build spots unlocked for free at start.
        """
        self.grid = [
            [0 for _ in range(self.cols)]
            for _ in range(self.rows)
        ]

        self.path_waypoints = [
            (0, 4),
            (3, 4),
            (3, 1),
            (7, 1),
            (7, 7),
            (11, 7),
            (11, 3),
            (14, 3)
        ]

        self._mark_path_on_grid()
        self._generate_build_spots()
        self._split_free_locked(free_count)

    def _mark_path_on_grid(self):
        """Mark path tiles on the grid based on waypoints."""
        for i in range(len(self.path_waypoints) - 1):
            start = self.path_waypoints[i]
            end = self.path_waypoints[i + 1]
            self._mark_line(start, end)

    def _mark_line(self, start, end):                                                                                                                           
        """Mark a straight line between two waypoints on the grid.

        Args:
            start: Starting (col, row) tuple.
            end: Ending (col, row) tuple.
        """
        col_start, row_start = start
        col_end, row_end = end

        if col_start == col_end:
            step = 1 if row_end > row_start else -1
            for r in range(row_start, row_end + step, step):
                self.grid[r][col_start] = 1
        elif row_start == row_end:
            step = 1 if col_end > col_start else -1
            for c in range(col_start, col_end + step, step):
                self.grid[row_start][c] = 1

    def _generate_build_spots(self):
        """Generate valid build spots adjacent to the path.

        Produces roughly half the possible adjacent tiles, distributed
        evenly along the path so that the start, middle, and end all
        have buildable locations.
        """
        path_tiles = set()
        for r in range(self.rows):
            for c in range(self.cols):
                if self.grid[r][c] == 1:
                    path_tiles.add((c, r))

        spawn_col, spawn_row = self.path_waypoints[0]
        base_col, base_row = self.path_waypoints[-1]
        exclusion = set()
        for ec, er in [(spawn_col, spawn_row), (base_col, base_row)]:
            for dc in range(-1, 2):
                for dr in range(-1, 2):
                    exclusion.add((ec + dc, er + dr))

        all_candidates = []
        for col, row in path_tiles:
            neighbors = [
                (col - 1, row), (col + 1, row),
                (col, row - 1), (col, row + 1)
            ]
            for nc, nr in neighbors:
                if (0 <= nc < self.cols and 0 <= nr < self.rows
                        and self.grid[nr][nc] == 0
                        and (nc, nr) not in path_tiles
                        and (nc, nr) not in all_candidates
                        and (nc, nr) not in exclusion):
                    all_candidates.append((nc, nr))

        target = max(8, len(all_candidates) * 6 // 10)

        path_order = self._get_path_tile_order()
        scored = []
        for spot in all_candidates:
            best = self.cols + self.rows
            for idx, pt in enumerate(path_order):
                d = abs(spot[0] - pt[0]) + abs(spot[1] - pt[1])
                if d < best:
                    best = d
                    score = idx
            scored.append((score, spot))
        scored.sort(key=lambda t: t[0])

        rng = random.Random(42)
        n_zones = 5
        zone_size = max(1, len(scored) // n_zones)
        selected = []
        for z in range(n_zones):
            start = z * zone_size
            end = min(len(scored), start + zone_size)
            zone = [s[1] for s in scored[start:end]]
            rng.shuffle(zone)
            pick = max(1, len(zone) * target // len(all_candidates))
            selected.extend(zone[:pick])

        remaining = [s[1] for s in scored if s[1] not in selected]
        rng.shuffle(remaining)
        while len(selected) < target and remaining:
            selected.append(remaining.pop())

        self.build_spots = selected

    def _get_path_tile_order(self):
        """Return path tiles in walk order from start to end."""
        ordered = []
        for i in range(len(self.path_waypoints) - 1):
            sc, sr = self.path_waypoints[i]
            ec, er = self.path_waypoints[i + 1]
            if sc == ec:
                step = 1 if er > sr else -1
                for r in range(sr, er + step, step):
                    if (sc, r) not in ordered:
                        ordered.append((sc, r))
            else:
                step = 1 if ec > sc else -1
                for c in range(sc, ec + step, step):
                    if (c, sr) not in ordered:
                        ordered.append((c, sr))
        return ordered

    def _split_free_locked(self, free_count):
        """Split generated build spots into free and locked sets.

        Free spots are distributed evenly across map zones so that
        each area of the path has 1-2 free spots rather than all
        free spots clustering in one region.

        Args:
            free_count: Number of spots available for free.
        """
        if free_count >= len(self.build_spots):
            self.locked_spots = []
            return

        zone_cols = max(1, self.cols // 3)
        zone_rows = max(1, self.rows // 2)
        zones = {}
        for spot in self.build_spots:
            zx = spot[0] // zone_cols
            zy = spot[1] // zone_rows
            zones.setdefault((zx, zy), []).append(spot)

        rng = random.Random(42)
        for spots_in_zone in zones.values():
            rng.shuffle(spots_in_zone)

        free = []
        zone_keys = sorted(zones.keys())
        round_robin_idx = 0
        while len(free) < free_count and round_robin_idx < max(
                len(v) for v in zones.values()):
            for key in zone_keys:
                if len(free) >= free_count:
                    break
                bucket = zones[key]
                if round_robin_idx < len(bucket):
                    free.append(bucket[round_robin_idx])
            round_robin_idx += 1

        free_set = set(free)
        locked = [s for s in self.build_spots if s not in free_set]
        self.build_spots = free
        self.locked_spots = locked

    def is_build_spot(self, col, row):
        """Check if a grid position is a valid (unlocked) build spot.

        Args:
            col: Column index.
            row: Row index.

        Returns:
            True if the position is an unlocked build spot.
        """
        return (col, row) in self.build_spots

    def is_locked_spot(self, col, row):
        """Check if a grid position is a locked build spot.

        Args:
            col: Column index.
            row: Row index.

        Returns:
            True if the position is a locked spot.
        """
        return (col, row) in self.locked_spots

    def unlock_spot(self, col, row):
        """Unlock a locked build spot, making it available for tower placement.

        Args:
            col: Column index.
            row: Row index.

        Returns:
            True if the spot was successfully unlocked.
        """
        if (col, row) in self.locked_spots:
            self.locked_spots.remove((col, row))
            self.build_spots.append((col, row))
            return True
        return False

    def is_path_tile(self, col, row):
        """Check if a grid position is part of the enemy path.

        Args:
            col: Column index.
            row: Row index.

        Returns:
            True if the position is a path tile.
        """
        if 0 <= row < self.rows and 0 <= col < self.cols:
            return self.grid[row][col] == 1
        return False

    def get_pixel_pos(self, col, row):
        """Convert grid coordinates to pixel coordinates (center of tile).

        Args:
            col: Column index.
            row: Row index.

        Returns:
            Tuple (x, y) pixel position at center of the tile.
        """
        x = col * self.tile_size + self.tile_size // 2
        y = row * self.tile_size + self.tile_size // 2
        return (x, y)

    def get_grid_pos(self, pixel_x, pixel_y):
        """Convert pixel coordinates to grid coordinates.

        Args:
            pixel_x: X pixel position.
            pixel_y: Y pixel position.

        Returns:
            Tuple (col, row) grid position.
        """
        col = pixel_x // self.tile_size
        row = pixel_y // self.tile_size
        return (col, row)

    def get_path_pixel_waypoints(self):
        """Get path waypoints in pixel coordinates.

        Returns:
            List of (x, y) tuples in pixel coordinates.
        """
        pixel_waypoints = []
        for col, row in self.path_waypoints:
            pixel_waypoints.append(self.get_pixel_pos(col, row))
        return pixel_waypoints

    def remove_build_spot(self, col, row):
        """Remove a build spot after a tower is placed.

        Args:
            col: Column index.
            row: Row index.
        """
        if (col, row) in self.build_spots:
            self.build_spots.remove((col, row))

    def add_build_spot(self, col, row):
        """Re-add a build spot when a tower is sold.

        Args:
            col: Column index.
            row: Row index.
        """
        if (col, row) not in self.build_spots and not self.is_path_tile(col, row):
            self.build_spots.append((col, row))
