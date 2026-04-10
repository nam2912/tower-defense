# Tower Defense Game

A 2D tower defense game built with Python and Pygame.

## Setup

```bash
pip install -r requirements.txt
python main.py
```

## Project Structure

```
├── main.py              # Entry point, game loop
├── config.py            # Game configuration (no global vars)
├── enums.py             # TowerType, EnemyType, GameState, SoldierState
├── game_manager.py      # Game state controller
├── game_map.py          # Tile grid, path, build spots
├── tower.py             # Tower, ArtilleryTower, BarracksTower
├── enemy.py             # Enemy class + factory function
├── soldier.py           # Soldier AI (state machine)
├── wave_manager.py      # Wave spawning and progression
├── renderer.py          # Pygame rendering and UI
├── requirements.txt     # Dependencies
└── assets/              # Images, sounds, fonts
```
