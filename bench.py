# ===== bench: test one job on its own and print the numbers =====
# Stop main first. Change the line at the bottom, then press play on THIS
# window. Results go to the output window (and output.txt).
#
# For a fair before/after comparison that doesn't touch your real farm, use
# simulate() (needs the Simulation unlock), e.g.:
#   simulate("bench", Unlocks, {Items.Cactus: 10000000, Items.Carrot: 10000000}, {}, 1, 64)
# Same seed = same random apples/pumpkin deaths, so two versions can be compared.

from config import HAY, WOOD, FERT, CARROT, PUMPKIN, CACTUS, SUN, MAZE, DINO
from config import POWER_MIN
from jobs import field_round, pumpkin_round, extra
from planner import plan
from mazes import do_mazes
from dino import do_dino
import stats

def ensure_power(seconds):
	# Top up Power BEFORE a bench, never during one, so every test runs at
	# full (doubled) drone speed the whole way through. 32 drones burn about
	# 1900 Power a minute, so aim for ~2200 per minute of benching.
	# Gives up after 60 rounds, just in case.
	target = POWER_MIN
	if seconds * 37 > target:
		target = seconds * 37
	tries = 0
	while num_items(Items.Power) < target and tries < 60:
		field_round(plan(Items.Power), dict())
		tries += 1
	quick_print("bench starting with Power:", num_items(Items.Power))

def ensure_carrots(seconds):
	# Pumpkins cost carrots to plant. 32 drones on 7x7 blocks plant roughly
	# 12000 pumpkins a minute (deaths included), so stock up for the whole
	# bench first. Carrots before Power: farming carrots burns Power.
	cost = get_cost(Entities.Pumpkin)
	tries = 0
	for item in cost:
		target = cost[item] * 12000 * seconds / 60
		while num_items(item) < target and tries < 60:
			field_round(plan(item), dict())
			tries += 1
		quick_print("bench starting with", item, ":", num_items(item), "(want", target, ")")

def bench_crop(mode, rounds):
	ensure_power(rounds * 60)
	wants = dict()
	for r in range(rounds):
		token = stats.start()
		field_round(mode, wants)
		stats.finish(mode, token, extra)
	stats.report()

def bench_pumpkin(rounds, seconds, patience, gap):
	# patience = extra checks to wait for a block to merge before taking pieces
	# gap = grass strip between blocks (0 = blocks touch)
	ensure_carrots(rounds * seconds)
	ensure_power(rounds * seconds)
	for r in range(rounds):
		for name in list(extra):
			extra.pop(name)
		token = stats.start()
		pumpkin_round(seconds, patience, gap, 0)
		stats.finish(PUMPKIN, token, extra)
	stats.report()

def bench_snake():
	ensure_power(300)
	token = stats.start()
	stats.finish(DINO, token, do_dino())
	stats.report()

def bench_maze():
	ensure_power(300)
	token = stats.start()
	stats.finish(MAZE, token, do_mazes())
	stats.report()

# ---- pick one, then press play on this window ----
bench_pumpkin(3, 60, 2, 1)   # gaps + two drones per block (16 blocks x 2 = 32 drones)
# bench_pumpkin(3, 60, 2, 0)   # no gaps, one drone per block (25 blocks)
# bench_crop(PUMPKIN, 3)
# bench_crop(CACTUS, 1)
# bench_snake()
# bench_maze()
