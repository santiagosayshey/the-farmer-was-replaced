# ===== lb_run: start a leaderboard run =====
# Stop main first, then press play on THIS window.
# Try it as a free practice run first: comment out leaderboard_run and
# uncomment simulate (same starting conditions, nothing gets uploaded).
# The last number speeds up the clock; runs repeat until 2 simulated hours.

leaderboard_run(Leaderboards.Pumpkins, "lb_pumpkins", 64)
# leaderboard_run(Leaderboards.Dinosaur, "lb_dino", 64)
# simulate("lb_dino", Unlocks, {Items.Cactus: 1000000000, Items.Power: 1000000000}, {}, -1, 64)
# simulate("lb_pumpkins", Unlocks, {Items.Carrot: 1000000000, Items.Power: 1000000000, Items.Water: 1000000}, {}, -1, 64)
