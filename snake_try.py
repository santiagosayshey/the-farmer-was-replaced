# ===== snake_try: one snake with a given shortcut cut-off =====
# Don't press play on this one: snake_lab runs it inside simulate() and
# hands it CUT (share of the farm to keep cutting corners until).

from dino import do_dino

t0 = get_time()
do_dino(CUT)
quick_print("SNAKE TRY cut", CUT, ":", get_time() - t0, "game seconds, bones", num_items(Items.Bone))
