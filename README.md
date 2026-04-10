# Tower Defense Game

A 2D tower defense game built with **Python 3** and **Pygame**, inspired
by Kingdom Rush. Players place and upgrade towers along an enemy path to
defend their base castle through infinite rounds of increasing difficulty.

**Student:** TRAN ANH TUAN
**Student ID:** SWD00440
**Course:** Introduction to Programming

---

## How to Run

```bash
# Create virtual environment (recommended on macOS)
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run the game
python3 main.py
```

---

## Controls

| Action | Input |
| --- | --- |
| Start game | SPACE |
| Select tower type | Click tower icon at bottom bar, or keys 1-0 |
| Place tower | Click a build spot (stone platform) on the map |
| Upgrade / sell tower | Click a placed tower, then use radial menu |
| Upgrade base castle | Click the castle, then use radial menu |
| Deselect | ESC or right-click |
| Pause / resume | Click pause button (top-right) |
| Speed toggle (x1/x2/x3) | Click speed button (top-right) |
| Skip slow round | Click SKIP button (appears after 8s idle) |
| Next round / retry | SPACE (on round complete/failed screen) |

---

## Game Features

### Towers (10 types, 15 upgrade levels each)

| Tower | Unlock | Cost | Mechanic |
| --- | --- | --- | --- |
| Archer | R1 | 50 | Fast single-target damage |
| Barracks | R1 | 70 | Spawns 3 soldiers that block enemies on path |
| Mage | R1 | 100 | Magic damage, ignores armor |
| Artillery | R1 | 115 | AOE splash damage |
| Freeze | R5 | 120 | Slows enemies |
| Poison | R10 | 120 | Damage-over-time, ignores armor |
| Ballista | R15 | 130 | Long-range piercing bolts |
| Tesla | R20 | 160 | Chain lightning arcing between enemies |
| Necromancer | R25 | 200 | Lifesteal heals base, ignores armor |
| Laser | R30 | 250 | High single-target beam, ignores armor |

Each tower has **15 upgrade levels** with a tiered star system:
- Lv 1-5: gold stars
- Lv 6-10: orange stars
- Lv 11-15: red stars

### Enemies (5 types)

| Enemy | Description |
| --- | --- |
| Grunt | Balanced stats, carries a club |
| Runner | Fast wolf-like creature, low HP |
| Armored | Slow dark knight, high HP and armor |
| Bomber | Goblin with TNT barrel, damages towers |
| Boss | Demon lord, massive HP, appears every 5 rounds |

Enemy HP scales **exponentially** (1.15x per round). Speed and armor
scale linearly with caps.

### Core Mechanics

- **Infinite rounds** with dynamic difficulty scaling
- **Base HP / Armor** system with 5 upgrade levels
- **Tower HP / Armor** system (towers can be destroyed by bombers)
- **Soldier blocking** — barracks soldiers intercept enemies on the path
- **Progressive tower unlocks** every 5 rounds
- **Radial menus** for upgrade and sell actions
- **Skip round** button with HP penalty for slow rounds
- **Particle effects**, floating damage numbers, projectile trails

---

## Project Structure

```
tower-defense/
├── main.py              # Entry point, game loop (fixed-timestep)
├── config.py            # Data-driven game configuration (no globals)
├── enums.py             # TowerType, EnemyType, GameState, SoldierState
├── game_manager.py      # Central game state coordinator (Mediator)
├── game_map.py          # Tile grid, path waypoints, build spots
├── tower.py             # Tower base class + 8 subclasses + factory
├── enemy.py             # Enemy class + factory with round scaling
├── soldier.py           # Soldier AI finite state machine
├── wave_manager.py      # Wave spawning and round generation
├── renderer.py          # All Pygame rendering and UI drawing
├── requirements.txt     # Dependencies (pygame>=2.5.0)
├── README.md            # This file
├── REQ.md               # Assignment requirements and rubric
└── REFERENCES.md        # Design pattern citations and asset sources
```

---

## Design Patterns Used

| Pattern | Module | Purpose |
| --- | --- | --- |
| Factory Method | `enemy.py`, `tower.py` | Create entities by type without exposing construction |
| State (FSM) | `soldier.py`, `game_manager.py` | Discrete state transitions with dedicated handlers |
| Mediator | `game_manager.py` | Central coordinator preventing direct module coupling |
| Inheritance / Polymorphism | `tower.py` | 8 tower subclasses override attack/upgrade behavior |
| Game Loop | `main.py` | Fixed-timestep input/update/render cycle |
| Data-Driven Design | `config.py` | All balance data in a dictionary, not hard-coded |
| Dependency Injection | All modules | Config passed via constructors, no global variables |
| Separation of Concerns | `renderer.py` | Rendering isolated from game logic (Model-View) |
| Queue-Based Spawning | `wave_manager.py` | Wave as a queue of enemy types dequeued at intervals |
| Surface Caching | `renderer.py` | Pre-rendered terrain cache for performance |
| Particle System | `renderer.py` | Lightweight transient visual effects |

Full citations with academic sources are in `REFERENCES.md`.

---

## Assignment Constraints

This project satisfies all 7 core requirements from the assignment brief:

1. **Functional decomposition** — 10 modules, each with focused functions
2. **Arrays and records** — lists for entities, classes for structured data
3. **Structured programming** — sequence, selection, repetition throughout
4. **Coding conventions** — snake_case functions, PascalCase classes, consistent formatting
5. **No global variables** — all data passed via function/constructor parameters
6. **No goto statements**
7. **Code understanding** — full docstrings on all modules, classes, and methods

---

## Dependencies

- **Python** >= 3.10
- **Pygame** >= 2.5.0

No other third-party libraries are used. All sprites and visual effects
are drawn procedurally using Pygame primitives — no external image,
sound, or font assets are bundled.
