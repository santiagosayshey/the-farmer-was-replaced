# ===== lb_pumpkins: the pumpkin leaderboard run =====
# Don't press play on this one: lb_run starts it inside leaderboard_run().
# Goal: own 200,000,000 pumpkins. Everyone stops the moment we get there.

from config import PUMPKIN_PATIENCE, PUMPKIN_GAP
from jobs import pumpkin_round

GOAL = 200000000
t0 = get_time()
while num_items(Items.Pumpkin) < GOAL:
	pumpkin_round(3600, PUMPKIN_PATIENCE, PUMPKIN_GAP, GOAL)
quick_print("LEADERBOARD pumpkins:", num_items(Items.Pumpkin), "in", get_time() - t0, "s")
