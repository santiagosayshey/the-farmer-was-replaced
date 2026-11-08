# ===== run: press play for everything except the farm itself =====
# Stop main first. Change the name in the LAST LINE, then press play.
#
#   Sandbox (your farm isn't touched, nothing uploaded):
#     "lb_pumpkins", "lb_dino"     leaderboard practice
#     "snake_compare"              snake settings side by side
#     "lab_water", "lab_ops", "lab_snake_cost", "lab_cure", ...  experiments
#   Real farm:
#     "bench_pumpkin", "bench_sun", "bench_snake", "bench_maze"
#   Real leaderboard runs (uploads a time):
#     "real_pumpkins", "real_dino"

import bench
import config

def go(name):
	if name == "bench_pumpkin":
		bench.bench_pumpkin(3, 60, 2, 1)
	elif name == "bench_sun":
		bench.bench_crop(config.SUN, 3)
	elif name == "bench_snake":
		bench.bench_snake()
	elif name == "bench_maze":
		bench.bench_maze()
	elif name == "real_pumpkins":
		leaderboard_run(Leaderboards.Pumpkins, "task", 64)
	elif name == "real_dino":
		leaderboard_run(Leaderboards.Dinosaur, "task", 64)
	else:
		# sandbox: leaderboard practice gets that board's exact starting items
		items = {Items.Carrot: 1000000000, Items.Cactus: 1000000000, Items.Hay: 1000000000, Items.Wood: 1000000000, Items.Pumpkin: 1000000000, Items.Water: 1000000, Items.Fertilizer: 1000000, Items.Weird_Substance: 1000000, Items.Power: 1000000000}
		if name == "lb_pumpkins":
			items = {Items.Carrot: 1000000000, Items.Power: 1000000000, Items.Water: 1000000}
		elif name == "lb_dino":
			items = {Items.Cactus: 1000000000, Items.Power: 1000000000}
		secs = simulate("task", Unlocks, items, {"JOB": name}, 1, 64)
		quick_print("RUN", name, "took", secs, "game seconds")

go("snake_compare")
