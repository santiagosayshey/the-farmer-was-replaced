# The Farmer Was Replaced: auto farm

Fully automated farm for *The Farmer Was Replaced*. Run `main`.

| File | What it does |
|---|---|
| `main` | The loop: plan, farm a round, measure, repeat |
| `config` | All settings: modes, upgrade values, Power target, maze cycles |
| `planner` | Measures real income rates, picks the unlock with the best payback, works out the crop chain |
| `jobs` | Drone jobs and fork/join (column leaders, half-columns with 32+ drones) |
| `crops` | What happens on a single tile, including polyculture companions |
| `mazes` | Shared-map maze reuse with drones guarding zones |
| `dino` | Dinosaur snake on a loop that covers every square, for bones |
| `status` | Status line in the output window + hat status lights |
| `util` | `goto`, `water`, `drones` |

## Setup (Windows)
1. Save folder: `%USERPROFILE%\AppData\LocalLow\TheFarmerWasReplaced\TheFarmerWasReplaced\Saves\<your save>`
2. Turn on **File Watcher** in the game settings so it reloads files changed outside the game.
3. Pull updates with `git pull`.
