# ===== bench: test one job on its own and print the numbers =====
# Stop main first. Change the line at the bottom, then press play on THIS
# window. Results go to the output window (and output.txt).
#
# For a fair before/after comparison that doesn't touch your real farm, use
# simulate() (needs the Simulation unlock), e.g.:
#   simulate("bench", Unlocks, {Items.Cactus: 10000000, Items.Carrot: 10000000}, {}, 1, 64)
# Same seed = same random apples/pumpkin deaths, so two versions can be compared.

from config import HAY, WOOD, FERT, CARROT, PUMPKIN, CACTUS, SUN, MAZE, DINO
from jobs import field_round, extra
from mazes import do_mazes
from dino import do_dino
import stats

def bench_crop(mode, rounds):
	wants = dict()
	for r in range(rounds):
		token = stats.start()
		field_round(mode, wants)
		stats.finish(mode, token, extra)
	stats.report()

def bench_snake():
	token = stats.start()
	stats.finish(DINO, token, do_dino())
	stats.report()

def bench_maze():
	token = stats.start()
	stats.finish(MAZE, token, do_mazes())
	stats.report()

# ---- pick one, then press play on this window ----
bench_crop(PUMPKIN, 3)
# bench_crop(CACTUS, 1)
# bench_snake()
# bench_maze()
