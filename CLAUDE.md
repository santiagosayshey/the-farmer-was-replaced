# CLAUDE.md: The Farmer Was Replaced auto farm

You're working in the user's **save folder** for the game *The Farmer Was Replaced* (TFWR), on Windows. Every `.py` file here is a code window in the game. The game's **File Watcher** is on, so your edits show up in the game straight away. The user presses play in the game and pastes the output back to you. You can't run the game yourself.

## About the user
- Has ADHD. Keep answers **short, plain and direct**. When teaching, use small steps.
- Wants you to **look things up and read the docs** rather than guess. Don't invent game mechanics. Say "I don't know, let's test it" instead.
- Is happy for you to explore and be wrong. **Don't change direction on your own** (for example, jumping to a real leaderboard run in the middle of testing). Ask first.
- Always tell them **exactly what to press** ("press play on `run`"). Never leave them guessing what to run.

## Hard rules
1. **No new windows.** Every window is a module named after the window, and the game has no folders. A new file only survives if the user creates a window with that name in the game first, otherwise `save.json` deletes it. So:
   - A new experiment is a function in `lab` plus one line in `task.pick()`.
   - A new real-farm test is a function in `bench` plus one line in `run.go()`.
2. **Test in the game's own sandbox, not in copies of the game you write in Python.** Earlier homemade simulators were wrong in ways that took longer to find than the thing being tested. Use `simulate()` through `run`. It returns elapsed game seconds.
3. **Don't touch the game's own files**: `save.json`, `__builtins__.py`, `output.txt`. These are git-ignored. **Read `__builtins__.py`** for the exact API; it's the game's own list of every function.
4. Use `import module` and `module.name`. Startup code goes only in `main`, `run` and `task`.
5. Commit to git after each working change, with clear messages, so the user can roll back.

## How the user runs things
- **`main`**: the full automated farm (planner + every crop). Press play.
- **`run`**: everything else. Its last line picks the job, e.g. `go("snake_compare")`:
  - Sandbox (farm untouched): `"lb_pumpkins"`, `"lb_dino"` (leaderboard practice), `"snake_compare"`, `"lab_water"`, `"lab_ops"`, `"lab_snake_cost"`, `"lab_cure"`, ...
  - Real farm: `"bench_pumpkin"`, `"bench_sun"`, `"bench_snake"`, `"bench_maze"`
  - Real leaderboard runs (upload a time): `"real_pumpkins"`, `"real_dino"`
- **`task`**: never pressed. It's what `simulate()` and `leaderboard_run()` execute. It recognises a leaderboard from the starting items (carrots only means pumpkins, cactus only means dinosaur). Other jobs get their name through `simulate(..., {"JOB": name}, ...)`.

## Files
| File | What it is |
|---|---|
| `config` | All settings |
| `planner` | Measures income rates, picks the unlock with the best payback, works out crop chains |
| `jobs` | Drone jobs, fork/join, pumpkin blocks, sunflowers |
| `crops` | One tile's logic, polyculture |
| `mazes` | Shared-map maze solving and reuse |
| `dino` | Snake (Hamiltonian loop plus shortcuts) |
| `status`, `stats` | Status lines and per-job stats |
| `bench`, `lab` | Libraries: real-farm tests and sandbox experiments |
| `util` | `goto`, `goto_near` (shortest path, wraps), `water`, `drones` |

## Measured facts (from real game runs)
- Actions (move, plant, harvest, use_item, ...) cost **200 ticks**. Checks and most code cost **about 1 tick per operation**. `tile(PUMPKIN)` on a grown pumpkin is about 13 ticks.
- About 3,000 ticks per second in the sandbox without Power, about 6,000 with Power.
- Pumpkins: grow in about 2s dry and about 0.26s at full water; growth time is random (roughly 0.13–0.4s soaked). About 20–23% die when they finish growing. A grown live pumpkin never dies afterwards. Planting straight onto a dead pumpkin works.
- Water: one use adds 0.25 (max 1), and soil dries about 1% per second. `water()` tops up below 0.8, so after warm-up most plantings skip watering.
- Giant pumpkins: any fully grown square merges. Yield is n³ up to 5×5, then 6 per tile (n² × 6). `measure()` gives the same id across one giant. Infection is per tile, even inside a giant. Fertilizer makes growth instant but infects; an infected tile gives half its share as Weird Substance. Weird Substance flips the infection of a tile and its 4 neighbours (curing a 6×6 is a Lights Out puzzle with a 28-press solution, which works). Fertilizer is passive only (about 0.8/s here), far too little for pumpkins.
- Snake: a move costs about 400 ticks at the start, 3% less per apple (rounded down), **flat at 33 ticks** from about 85 apples on. Bones = 32 × length² (a full 32×32 snake gives exactly the leaderboard's 33,488,928). One full snake is better than several partial ones.

## Current state and results
- **Pumpkins:** 1-tile grass gaps between 6×6 blocks, 2 drones per block (`pair_block`: to-do list, nearest first, merge check on its own outer column, helping). About **24M/min**. Leaderboard: 8:42, #308. The top is about 5:43, roughly 35M/min. Tried and lost: 7×7 (tie), 8×8 and 10×10 loops (worse), babysitting dead tiles, small-patch finishing, fertilizer.
- **Snake:** zig-zag Hamiltonian loop with shortcuts until 20% of the farm (`SNAKE_SHORTCUT_UNTIL`), then a 2-line follow loop. Real sandbox times: 15%–30% about 960s (best), 50% about 1,165s, 100% about 3,000s. Leaderboard: 15:55, #248; top 2 about 5:15, #3–10 7:46–10:08. Tried and lost: greedy BFS with a tail check (too much thinking), shortcuts checked only by `can_move()` (boxed in at length about 65, because it jumped past the tail into gaps in the body).
- **Snake ideas not tried yet:** (a) the `can_move()` check plus a cap so no jump is longer than the free space ahead (free space is roughly total minus apples eaten); (b) deciding shortcuts once per row instead of every step.
- **Sunflowers:** level-by-level harvest on a shared-clock timetable, each drone in its own columns.
- **Missing achievements:** Feels Good (pet the piggy), Healer (cure an infected plant), Master Acrobat (1000 flips), Chaos (20 windows open: the user does this by hand), Stack Overflow, Circular Import, Wrong Order (sort a full field of cacti the wrong way), Fashion Show (5 hats on 5 drones), Size Matters and Dino Master (one full snake on the **real** farm should give both), Big Bone/Wood/Hay/Carrot/Cactus/Gold Farmer (just farming), Hay/Carrot/Wood Master (per-minute targets), What now? (unlock everything), Full Automation (Fastest Reset leaderboard). Sandbox runs don't count towards achievements.

## Game docs worth knowing
- `simulate(filename, unlocks, items, globals, seed, speedup)` returns elapsed game seconds. `globals` sets global variables in that file.
- `leaderboard_run(Leaderboards.X, filename, speedup)` takes no globals. Runs repeat until 2 simulated hours, then upload the average. The program must end by itself.
- The leaderboard goals are in `task` (pumpkins 200,000,000; bones 33,488,928).
