# ===== run: everything except the farm itself =====
# Stop main, uncomment ONE line at the bottom, press play on THIS window.
# Sandbox and leaderboard jobs: set TASK in config first (see the list there).

from config import TASK
from bench import bench_pumpkin, bench_crop, bench_snake, bench_maze
from config import PUMPKIN, CACTUS, SUN

def items_for(task):
	# the leaderboard's starting items, so practice matches the real run
	if task == "lb_pumpkins":
		return {Items.Carrot: 1000000000, Items.Power: 1000000000, Items.Water: 1000000}
	if task == "lb_dino" or task == "snake_compare":
		return {Items.Cactus: 1000000000, Items.Power: 1000000000}
	return {Items.Carrot: 1000000000, Items.Cactus: 1000000000, Items.Hay: 1000000000, Items.Wood: 1000000000, Items.Pumpkin: 1000000000, Items.Water: 1000000, Items.Fertilizer: 1000000, Items.Weird_Substance: 1000000, Items.Power: 1000000000}

def practice():
	# sandbox: same rules, nothing uploaded, your farm untouched
	simulate("task", Unlocks, items_for(TASK), {}, -1, 64)

def real():
	# the actual leaderboard run (repeats until 2 simulated hours, then uploads)
	if TASK == "lb_pumpkins":
		leaderboard_run(Leaderboards.Pumpkins, "task", 64)
	elif TASK == "lb_dino":
		leaderboard_run(Leaderboards.Dinosaur, "task", 64)
	else:
		quick_print("run: TASK", TASK, "isn't a leaderboard job")

# ---- pick ONE ----
practice()
# real()
# bench_pumpkin(3, 60, 2, 1)     # pumpkins on the real farm (tops up carrots and Power first)
# bench_crop(SUN, 3)             # sunflowers on the real farm
# bench_snake()
# bench_maze()
