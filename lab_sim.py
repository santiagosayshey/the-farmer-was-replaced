# ===== lab_sim: run the lab in the sandbox (your real farm isn't touched) =====
# Stop main first, then press play on this window. The last number speeds
# up the sandbox clock (16x) so it finishes quickly; times are in game seconds.
simulate("lab", Unlocks, {Items.Carrot: 1000000000, Items.Cactus: 1000000000, Items.Hay: 1000000000, Items.Wood: 1000000000, Items.Pumpkin: 1000000000, Items.Water: 1000000, Items.Fertilizer: 1000000, Items.Weird_Substance: 1000000, Items.Power: 0}, {}, 1, 16)
