"""Wave manager module.

Generates infinite rounds of enemies with progressive scaling.
Each round increases enemy count, HP, speed, armor, and boss frequency.

Design patterns: Queue-Based Spawning, Data-Driven Design.
See REFERENCES.md for full citations.
"""

from enums import EnemyType
from enemy import create_enemy


class WaveManager:
    """Manages infinite enemy wave spawning with progressive difficulty.

    Attributes:
        config: Game configuration dictionary.
        round_number: Current round number (1-based).
        spawn_queue: List of EnemyType values waiting to spawn.
        spawn_timer: Countdown until next enemy spawn.
        spawn_interval: Seconds between enemy spawns.
        wave_active: Whether enemies are still spawning.
        round_active: Whether any enemies remain from the current round.
    """

    def __init__(self, config):
        """Initialize the wave manager.

        Args:
            config: Game configuration dictionary.
        """
        self.config = config
        self.round_number = 0
        self.spawn_queue = []
        self.spawn_timer = 0.0
        self.spawn_interval = 1.0
        self.wave_active = False
        self.round_active = False

    def start_round(self, round_number):
        """Start a specific round, generating enemies dynamically.

        Args:
            round_number: Round number to start (1-based).
        """
        self.round_number = round_number
        self.spawn_queue = self._generate_round(round_number)
        self.spawn_timer = 0.0
        self.spawn_interval = max(0.3, 1.0 - (round_number - 1) * 0.04)
        self.wave_active = True
        self.round_active = True

    def _generate_round(self, round_num):
        """Generate the enemy composition for a given round.

        Scaling rules:
        - Grunt count grows moderately each round.
        - Runners from R2, count grows slowly.
        - Armored from R4, count grows slowly.
        - Bombers from R7, they damage towers when passing.
        - Every 5 rounds is a BOSS round with stronger mega-boss(es).
        - After R15 the mix gets heavier with more armored + bombers.

        Args:
            round_num: Round number (1-based).

        Returns:
            List of EnemyType values for this round.
        """
        enemies = []

        grunt_count = 3 + round_num + round_num // 4
        enemies.extend([EnemyType.GRUNT] * grunt_count)

        if round_num >= 2:
            runner_count = max(1, (round_num - 1) // 2 + 1)
            enemies.extend([EnemyType.RUNNER] * runner_count)

        if round_num >= 4:
            armored_count = max(1, (round_num - 3) // 3 + 1)
            enemies.extend([EnemyType.ARMORED] * armored_count)

        if round_num >= 7:
            bomber_count = max(1, (round_num - 6) // 3)
            enemies.extend([EnemyType.BOMBER] * bomber_count)

        if round_num >= 5 and round_num % 5 == 0:
            boss_count = max(1, round_num // 10)
            enemies.extend([EnemyType.BOSS] * boss_count)

        if round_num > 15:
            extras = (round_num - 15) // 4
            enemies.extend([EnemyType.ARMORED] * extras)
            enemies.extend([EnemyType.BOMBER] * extras)

        if round_num > 25:
            heavy = (round_num - 25) // 5
            enemies.extend([EnemyType.BOSS] * heavy)

        return enemies

    def get_round_scaling(self):
        """Get the stat multipliers for the current round.

        Returns:
            Dict with 'hp', 'speed', 'armor', 'gold' scaling factors.
        """
        r = self.round_number
        return {
            "hp": 1.15 ** (r - 1),
            "speed": min(1.0 + (r - 1) * 0.02, 1.8),
            "armor": int((r - 1) * 0.5),
            "gold": 1.0 + (r - 1) * 0.03
        }

    def update(self, enemies, start_pos, dt):
        """Update spawning logic each frame.

        Args:
            enemies: List to append newly spawned enemies to.
            start_pos: Tuple (x, y) pixel position where enemies spawn.
            dt: Delta time in seconds.
        """
        if not self.wave_active:
            return

        if len(self.spawn_queue) == 0:
            self.wave_active = False
            return

        self.spawn_timer -= dt
        if self.spawn_timer <= 0:
            enemy_type = self.spawn_queue.pop(0)
            new_enemy = create_enemy(
                enemy_type, start_pos, self.config, self.round_number
            )
            enemies.append(new_enemy)
            self.spawn_timer = self.spawn_interval

    def is_round_clear(self, enemies):
        """Check if the current round is fully defeated.

        Args:
            enemies: List of Enemy instances.

        Returns:
            True if no spawn queue remains and no enemies alive.
        """
        if self.wave_active:
            return False
        alive_count = sum(1 for e in enemies if e.is_alive)
        return alive_count == 0

    def get_wave_info(self):
        """Get current round status information.

        Returns:
            Tuple (round_number, enemies_remaining_in_queue).
        """
        return (self.round_number, len(self.spawn_queue))

    def get_enemy_count_for_round(self, round_num=None):
        """Get total enemy count for a given round.

        Args:
            round_num: Round to check (defaults to current round).

        Returns:
            Total number of enemies in the round.
        """
        if round_num is None:
            round_num = self.round_number
        return len(self._generate_round(round_num))
