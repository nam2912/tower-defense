"""Tower Defense Game - Main Entry Point.

Initializes Pygame, sets up the game loop, and delegates to GameManager
for event handling, updates, and rendering. No global variables are used.

Design patterns: Game Loop.
See REFERENCES.md for full citations.
"""

import pygame
import sys
from config import get_config
from game_manager import GameManager


def create_screen(config):
    """Create and return the Pygame display surface.

    Args:
        config: Game configuration dictionary.

    Returns:
        Pygame display surface.
    """
    screen_config = config["screen"]
    screen = pygame.display.set_mode(
        (screen_config["width"], screen_config["height"])
    )
    pygame.display.set_caption(screen_config["title"])
    return screen


def run_game_loop(screen, config):
    """Run the main game loop.

    Args:
        screen: Pygame display surface.
        config: Game configuration dictionary.
    """
    clock = pygame.time.Clock()
    fps = config["screen"]["fps"]
    game_manager = GameManager(screen, config)

    running = True
    while running:
        dt = clock.tick(fps) / 1000.0

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            else:
                game_manager.handle_event(event)

        game_manager.update(dt)
        game_manager.render()
        pygame.display.flip()


def main():
    """Initialize Pygame and start the game."""
    pygame.init()
    config = get_config()
    screen = create_screen(config)

    run_game_loop(screen, config)

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
