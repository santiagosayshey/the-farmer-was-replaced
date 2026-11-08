# ===== lb_dino: the dinosaur leaderboard run =====
# Don't press play on this one: lb_run starts it inside leaderboard_run().
# Goal: 33,488,928 bones = one tail filling the whole 32x32 farm, which is
# exactly what one full snake does.

from dino import do_dino

t0 = get_time()
while num_items(Items.Bone) < 33488928:
	do_dino(-1)
quick_print("LEADERBOARD bones:", num_items(Items.Bone), "in", get_time() - t0, "s")
