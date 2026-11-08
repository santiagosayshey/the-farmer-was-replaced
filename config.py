# ===== config: all the settings and names in one place =====

# modes
HAY = 0
WOOD = 1
FERT = 2      # wood + fertilizer, makes Weird Substance
CARROT = 3
PUMPKIN = 4
CACTUS = 5
SUN = 6
MAZE = 7
DINO = 8      # dinosaur snake, makes bones

MODE_NAME = ["hay", "wood", "weird substance", "carrots", "pumpkins",
	"cactus", "sunflowers", "mazes", "dinosaurs"]
HAT_STATUS = True   # main drone wears a different hat for each job

BIG_MODES = [PUMPKIN, CACTUS, SUN]
POLY_MODES = [HAY, WOOD, CARROT]
BIG_CROP = {PUMPKIN: Entities.Pumpkin, CACTUS: Entities.Cactus, SUN: Entities.Sunflower}

# which crop makes which item
CROP = {
	Items.Carrot: Entities.Carrot,
	Items.Pumpkin: Entities.Pumpkin,
	Items.Cactus: Entities.Cactus,
	Items.Power: Entities.Sunflower
}
MODE_FOR = {
	Items.Hay: HAY,
	Items.Wood: WOOD,
	Items.Carrot: CARROT,
	Items.Pumpkin: PUMPKIN,
	Items.Cactus: CACTUS,
	Items.Power: SUN
}

# the item each mode produces (used to measure real income rates)
MODE_ITEM = {
	HAY: Items.Hay,
	WOOD: Items.Wood,
	FERT: Items.Weird_Substance,
	CARROT: Items.Carrot,
	PUMPKIN: Items.Pumpkin,
	CACTUS: Items.Cactus,
	SUN: Items.Power,
	MAZE: Items.Gold,
	DINO: Items.Bone
}

# items the planner understands
MODELED = [
	Items.Hay, Items.Wood, Items.Carrot, Items.Pumpkin,
	Items.Cactus, Items.Weird_Substance, Items.Gold, Items.Bone
]
TRACKED = [
	Items.Hay, Items.Wood, Items.Carrot, Items.Pumpkin,
	Items.Cactus, Items.Weird_Substance, Items.Gold, Items.Bone, Items.Power
]

# starting guesses: seconds of farming per 1 item. Replaced by real
# measurements after a few rounds, so these don't need to be accurate.
DEFAULT_OWN = {
	Items.Hay: 0.02,
	Items.Wood: 0.02,
	Items.Carrot: 0.05,
	Items.Pumpkin: 0.05,
	Items.Cactus: 0.002,
	Items.Weird_Substance: 2,
	Items.Gold: 0.05,
	Items.Bone: 0.001
}

# what each upgrade is worth: item -> how many times faster it gets.
# These are my best guesses. Tweak them if you know better!
VALUE = {
	Unlocks.Megafarm: {
		Items.Hay: 2, Items.Wood: 2, Items.Carrot: 2, Items.Pumpkin: 2,
		Items.Cactus: 2, Items.Weird_Substance: 2, Items.Gold: 1.3
	},
	Unlocks.Grass: {Items.Hay: 2},
	Unlocks.Trees: {Items.Wood: 2},
	Unlocks.Carrots: {Items.Carrot: 2},
	Unlocks.Pumpkins: {Items.Pumpkin: 2},
	Unlocks.Cactus: {Items.Cactus: 2},
	Unlocks.Fertilizer: {Items.Weird_Substance: 2},
	Unlocks.Polyculture: {Items.Hay: 2, Items.Wood: 2, Items.Carrot: 2},
	# bigger farm: bones, cactus and gold all scale with area, plain crops
	# gain a little because drones waste less time spawning and walking
	Unlocks.Expand: {
		Items.Bone: 1.5, Items.Cactus: 1.5, Items.Gold: 1.5, Items.Pumpkin: 1.05,
		Items.Hay: 1.1, Items.Wood: 1.1, Items.Carrot: 1.1
	},
	Unlocks.Mazes: {Items.Gold: 1.2},
	Unlocks.Dinosaurs: {Items.Bone: 1000},   # first unlock: bones go from impossible to possible (later levels count as 2x, see planner)
	Unlocks.Watering: {
		Items.Hay: 1.05, Items.Wood: 1.05, Items.Carrot: 1.05, Items.Pumpkin: 1.05
	}
}

# anything NOT in VALUE gets bought only if it costs less than this many
# seconds of farming
FLUFF_MAX = 60

UNLOCKS = [
	Unlocks.Auto_Unlock, Unlocks.Cactus, Unlocks.Carrots, Unlocks.Costs,
	Unlocks.Debug, Unlocks.Debug_2, Unlocks.Dictionaries, Unlocks.Dinosaurs,
	Unlocks.Expand, Unlocks.Fertilizer, Unlocks.Functions, Unlocks.Grass,
	Unlocks.Hats, Unlocks.Import, Unlocks.Lists, Unlocks.Loops, Unlocks.Mazes,
	Unlocks.Megafarm, Unlocks.Operators, Unlocks.Plant, Unlocks.Polyculture,
	Unlocks.Pumpkins, Unlocks.Senses, Unlocks.Simulation, Unlocks.Speed,
	Unlocks.Sunflowers, Unlocks.Timing, Unlocks.Trees, Unlocks.Utilities,
	Unlocks.Variables, Unlocks.Watering,
	Unlocks.Leaderboard, Unlocks.Top_Hat, Unlocks.The_Farmers_Remains
]

# late-game goals: always buy these as soon as we can afford them
GOALS = [Unlocks.Leaderboard, Unlocks.Top_Hat]

# farm toward these, but leave the button for you to press
MANUAL = [Unlocks.The_Farmers_Remains]

POWER_MIN = 3000   # top up sunflowers below this (32 drones burn ~1900 a minute)
FIELD_BUFFER = 1.5 # need this many fields' worth of seed cost before planting
MAZE_CYCLES = 300  # treasure grabs per maze before finishing it (max 300)
STUCK_LIMIT = 40   # give up on a big crop after this many rounds
SNAKE_SHORTCUT_UNTIL = 0.5   # snake cuts corners until it fills this much of the farm (real game: 0.5 = 1183s, 0.7 = 1675s)
REPLAN_EVERY = 5   # rounds between planner decisions (planning takes ~a second)
PUMPKIN_ROUND_SECONDS = 60  # each pumpkin round runs this long (tested: 60s beats 20s)
PUMPKIN_PATIENCE = 2  # extra sweeps to wait for a block to merge before taking the pieces
PUMPKIN_GAP = 1    # grass strip between blocks: every block merges into a full 6x6 (gaps + pairs passed 20M/min)
PUMPKIN_WATER = True  # water pumpkins when planting (8x faster growth, but costs a tick-heavy action per tile)
PUMPKIN_BLOCK = 6  # block width. 6 is the smallest that pays 6 per tile (tested: 7 ties, 8 and 10 are ~20% worse)
PUMPKIN_PAIRS = True  # two drones share each block when there are enough drones
PUMPKIN_LOOP = False  # drones walk a closed loop round the block, half a lap apart (needs an even PUMPKIN_BLOCK and a gap; 6x6: ~24M/min)
PUMPKIN_PAIR2 = True  # (when PUMPKIN_LOOP is off) pairs use the tuned half-block worker (sim: ~3% faster than the loop)
STATS_EVERY = 20   # print a stats summary every this many rounds

# ---------- the run / task windows ----------
# Which job the sandbox (practice) or a leaderboard run (real) does, in task:
#   "lb_pumpkins"   pumpkin leaderboard (200M pumpkins)
#   "lb_dino"       dinosaur leaderboard (one full snake)
#   "snake_compare" full snakes with different shortcut cut-offs
#   "lab_water", "lab_ops", "lab_snake_cost", "lab_cure", "lab_speed", ...
#                   any experiment in lab, by name
TASK = "lb_pumpkins"
