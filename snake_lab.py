# ===== snake_lab: compare snake settings in the real game's sandbox =====
# Stop main, then press play on THIS window. Each line runs one full snake
# with the same random seed (same apples), so the times compare fairly.
# Same starting items as the dinosaur leaderboard.

items = {Items.Cactus: 1000000000, Items.Power: 1000000000}
for cut in [0.5, 0.7, 0.85, 1.0]:
	simulate("snake_try", Unlocks, items, {"CUT": cut}, 7, 256)
