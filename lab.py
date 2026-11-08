# ===== lab: measure the game's real rules =====
# Run this INSIDE simulate() (see the lab_sim window) so the real farm isn't
# touched: set_world_size() clears the farm. Each experiment prints results
# to the output window. Send the output back so the simulations can be
# calibrated against the real game.

from dino import other_hat
from util import goto
from jobs import step_to
from crops import tile
from config import PUMPKIN

def wait_until_done():
	# stand still on a tile until the plant is grown or dead.
	# returns [seconds, "grown" / "dead"]
	t0 = get_time()
	while True:
		if get_entity_type() == Entities.Dead_Pumpkin:
			return [get_time() - t0, "dead"]
		if can_harvest():
			return [get_time() - t0, "grown"]

def avg(xs):
	if len(xs) == 0:
		return 0
	total = 0
	for x in xs:
		total += x
	return total / len(xs)


# ---------- 1. how fast does the drone run? ----------
def lab_speed():
	set_world_size(4)
	t0 = get_time()
	k0 = get_tick_count()
	for i in range(40):
		move(East)
	dt = get_time() - t0
	dk = get_tick_count() - k0
	quick_print("SPEED: 40 moves took", dt, "s and", dk, "ticks =", dk / dt, "ticks/s")
	t0 = get_time()
	for i in range(200):
		get_entity_type()
	quick_print("SPEED: 200 checks took", get_time() - t0, "s")


# ---------- 2. pumpkins: grow time, death rate, effect of water ----------
def lab_pumpkins(samples, watered):
	set_world_size(4)
	times = []
	deaths = 0
	for i in range(samples):
		if get_ground_type() != Grounds.Soil:
			till()
		plant(Entities.Pumpkin)
		if watered:
			while get_water() < 1 and num_items(Items.Water) > 0:
				use_item(Items.Water)
		result = wait_until_done()
		times.append(result[0])
		if result[1] == "dead":
			deaths += 1
		harvest()
	quick_print("PUMPKIN watered=", watered, ": avg grow", avg(times), "s, died", deaths, "of", samples)


# ---------- 3. trees: grow time alone vs with neighbours ----------
def lab_trees():
	set_world_size(4)
	# alone at (1,1)
	move(East)
	move(North)
	plant(Entities.Tree)
	t_alone = wait_until_done()[0]
	harvest()
	# with 4 tree neighbours
	for d in [North, East, South, West]:
		move(d)
		plant(Entities.Tree)
		if d == North:
			move(South)
		elif d == East:
			move(West)
		elif d == South:
			move(North)
		else:
			move(East)
	plant(Entities.Tree)
	t_crowded = wait_until_done()[0]
	quick_print("TREE: alone", t_alone, "s, with 4 tree neighbours", t_crowded, "s")


# ---------- 4. snake vs planted tiles (the bush-blocking idea) ----------
def bare_farm():
	# 4x4 farm, all soil (grass regrows on grassland, and apples won't spawn
	# on grass), drone back at (0, 0)
	set_world_size(4)
	for x in range(4):
		for y in range(4):
			if get_ground_type() != Grounds.Soil:
				till()
			move(North)
		move(East)

def lab_snake_plants():
	# a) do apples ever spawn on planted tiles? bushes on the right half,
	#    snake loops around the empty left half and notes where apples appear
	bare_farm()
	for x in range(4):
		for y in range(4):
			if get_pos_x() >= 2:
				plant(Entities.Bush)
			move(North)
		move(East)
	loop = [North, North, North, East, South, South, South, West]
	change_hat(Hats.Dinosaur_Hat)
	on_empty = 0
	on_bush = 0
	i = 0
	while i < 300:
		if get_entity_type() == Entities.Apple:
			a = measure()
			if a != None:
				if a[0] >= 2:
					on_bush += 1
				else:
					on_empty += 1
		if not move(loop[i % 8]):
			break
		i += 1
	quick_print("SNAKE: next apple on empty half", on_empty, "times, on bush half", on_bush, "times")
	change_hat(other_hat())

	# b) can the snake step onto a planted tile, and what happens to it?
	bare_farm()
	move(East)
	plant(Entities.Bush)
	move(West)
	change_hat(Hats.Dinosaur_Hat)
	ok = move(East)
	under = get_entity_type()
	quick_print("SNAKE: move onto a bush returned", ok, "| now standing on:", under)
	move(West)
	quick_print("SNAKE: after stepping off, that tile holds:", get_entity_type())
	change_hat(other_hat())

	# c) grassland instead of bushes: grass regrows by itself, so if it
	#    blocks apples, the ground type alone decides where apples can go.
	#    Left half soil, right half grassland (grass grows back on its own).
	bare_farm()
	for x in range(4):
		for y in range(4):
			if get_pos_x() >= 2:
				till()           # soil -> grassland
			move(North)
		move(East)
	quick_print("SNAKE: right half is now", get_ground_type(), "...")
	change_hat(Hats.Dinosaur_Hat)
	on_soil = 0
	on_grass = 0
	i = 0
	while i < 300:
		if get_entity_type() == Entities.Apple:
			a = measure()
			if a != None:
				if a[0] >= 2:
					on_grass += 1
				else:
					on_soil += 1
		if not move(loop[i % 8]):
			break
		i += 1
	quick_print("SNAKE: next apple on soil half", on_soil, "times, on grassland half", on_grass, "times")
	# can the snake walk over grass, and does grass come back behind the tail?
	ok = move(East)
	ok2 = move(East)
	quick_print("SNAKE: walking onto grassland returned", ok, ok2, "| standing on:", get_entity_type())
	change_hat(other_hat())


# ---------- 5. fertilizer on pumpkins ----------
def soak():
	while get_water() < 1 and num_items(Items.Water) > 0:
		use_item(Items.Water)

def lab_fert_tiles(samples, watered):
	# a) plant, (water), fertilize: how long until grown/dead now? same death rate?
	set_world_size(4)
	times = []
	instant = 0
	deaths = 0
	for i in range(samples):
		if get_ground_type() != Grounds.Soil:
			till()
		plant(Entities.Pumpkin)
		if watered:
			soak()
		use_item(Items.Fertilizer)
		e = get_entity_type()
		if e == Entities.Dead_Pumpkin or can_harvest():
			instant += 1
		result = wait_until_done()
		times.append(result[0])
		if result[1] == "dead":
			deaths += 1
		harvest()
	quick_print("FERT TILE watered=", watered, ": done instantly", instant, "of", samples, "| avg wait after fertilizing", avg(times), "s | died", deaths, "of", samples)

def fert_tile():
	# stay on this tile until it holds a grown, live pumpkin. returns fertilizer used
	used = 0
	while True:
		if get_entity_type() != Entities.Pumpkin:
			plant(Entities.Pumpkin)
			soak()
			use_item(Items.Fertilizer)
			used += 1
		if get_entity_type() == Entities.Pumpkin:
			if can_harvest():
				return used
			if wait_until_done()[1] == "grown":
				return used

def lab_fert_block(use_fert):
	# b) one drone builds and harvests a full 6x6 giant: time, pumpkins,
	#    weird substance and fertilizer used. Normal way = plant + water,
	#    then sweep replanting dead ones until everything is grown.
	set_world_size(6)
	for x in range(6):
		for y in range(6):
			if get_ground_type() != Grounds.Soil:
				till()
			move(North)
		move(East)
	p0 = num_items(Items.Pumpkin)
	w0 = num_items(Items.Weird_Substance)
	f0 = num_items(Items.Fertilizer)
	t0 = get_time()
	for x in range(6):
		for y in range(6):
			if use_fert:
				fert_tile()
			else:
				plant(Entities.Pumpkin)
				soak()
			if y < 5:
				if x % 2 == 0:
					move(North)
				else:
					move(South)
		move(East)
	sweeps = 0
	while True:
		all_good = True
		for x in range(6):
			for y in range(6):
				if get_entity_type() != Entities.Pumpkin:
					plant(Entities.Pumpkin)
					soak()
					all_good = False
				elif not can_harvest():
					all_good = False
				move(North)
			move(East)
		sweeps += 1
		if all_good:
			break
	# corners should now be one giant
	a = measure()
	for i in range(5):
		move(East)
	b = measure()
	merged = a != None and a == b
	t_grow = get_time() - t0
	harvest()
	quick_print("FERT BLOCK fert=", use_fert, ": merged", merged, "| seconds", t_grow, "| extra sweeps", sweeps - 1, "| pumpkins", num_items(Items.Pumpkin) - p0, "| weird substance", num_items(Items.Weird_Substance) - w0, "| fertilizer used", f0 - num_items(Items.Fertilizer))


# ---------- 6. curing infected giants with Weird Substance ----------
# Weird Substance toggles infection on the plant AND its 4 neighbours, so
# curing a whole fully-infected 6x6 is a "lights out" puzzle. These 28
# presses (solved offline) turn every tile of a 6x6 from infected to healthy.
CURE_6 = [[0, 0], [2, 0], [3, 0], [5, 0], [1, 1], [2, 1], [3, 1], [4, 1], [0, 2], [1, 2], [2, 2], [3, 2], [4, 2], [5, 2], [0, 3], [1, 3], [2, 3], [3, 3], [4, 3], [5, 3], [1, 4], [2, 4], [3, 4], [4, 4], [0, 5], [2, 5], [3, 5], [5, 5]]

def lab_cure(how):
	# how: "normal"  plant + water, no fertilizer (the reference)
	#      "fert"    every tile fertilized, no cure
	#      "one"     ONLY the corner tile fertilized (does one infected tile
	#                spoil the whole giant, or just its share?)
	#      "giant1"  every tile fertilized, then ONE Weird Substance on the
	#                finished giant (is a giant one plant with one infection?)
	#      "cure28"  every tile fertilized, then the 28-press pattern
	# 8x8 farm, block in the corner, so presses never wrap round onto the block
	set_world_size(8)
	for x in range(6):
		for y in range(6):
			goto(x, y)
			if get_ground_type() != Grounds.Soil:
				till()
	p0 = num_items(Items.Pumpkin)
	w0 = num_items(Items.Weird_Substance)
	t0 = get_time()
	for x in range(6):
		for y in range(6):
			goto(x, y)
			if how == "fert" or how == "giant1" or how == "cure28" or (how == "one" and x == 0 and y == 0):
				fert_tile()
			else:
				plant(Entities.Pumpkin)
				soak()
	# replant dead ones (only the unfertilized ones can still die)
	done = False
	while not done:
		done = True
		for x in range(6):
			for y in range(6):
				goto(x, y)
				if get_entity_type() != Entities.Pumpkin:
					plant(Entities.Pumpkin)
					soak()
					done = False
				elif not can_harvest():
					done = False
	presses = 0
	if how == "giant1":
		goto(0, 0)
		use_item(Items.Weird_Substance)
		presses = 1
	if how == "cure28":
		for p in CURE_6:
			goto(p[0], p[1])
			use_item(Items.Weird_Substance)
			presses += 1
	goto(0, 0)
	a = measure()
	goto(5, 0)
	b = measure()
	goto(0, 0)
	secs = get_time() - t0
	harvest()
	quick_print("CURE", how, ": merged", a != None and a == b, "| seconds", secs, "| presses", presses, "| pumpkins", num_items(Items.Pumpkin) - p0, "| weird substance", num_items(Items.Weird_Substance) - w0 + presses)


# ---------- 7. what does plain code cost? ----------
# Actions (move, plant, ...) cost 200 ticks. Does ordinary code (adding,
# calling a function, list work) cost ticks too? Ticks per item for each.
def nothing():
	return 0

def lab_ops():
	set_world_size(4)
	n = 1000
	k = get_tick_count()
	for i in range(n):
		pass
	quick_print("OPS: empty loop step", (get_tick_count() - k) / n, "ticks")
	x = 0
	k = get_tick_count()
	for i in range(n):
		x = x + 1
	quick_print("OPS: loop step with x = x + 1", (get_tick_count() - k) / n, "ticks")
	k = get_tick_count()
	for i in range(n):
		nothing()
	quick_print("OPS: loop step with an empty function call", (get_tick_count() - k) / n, "ticks")
	lst = []
	k = get_tick_count()
	for i in range(n):
		lst.append(i)
	quick_print("OPS: loop step with list.append", (get_tick_count() - k) / n, "ticks")
	k = get_tick_count()
	for i in range(n):
		get_entity_type()
	quick_print("OPS: loop step with get_entity_type()", (get_tick_count() - k) / n, "ticks")
	k = get_tick_count()
	for i in range(n):
		get_time()
	quick_print("OPS: loop step with get_time()", (get_tick_count() - k) / n, "ticks")
	k = get_tick_count()
	for i in range(100):
		step_to(get_pos_x(), get_pos_y())
	quick_print("OPS: step_to where I already am", (get_tick_count() - k) / 100, "ticks")
	# a grown, live pumpkin: what does one tile(PUMPKIN) visit cost?
	if get_ground_type() != Grounds.Soil:
		till()
	plant(Entities.Pumpkin)
	soak()
	while not (get_entity_type() == Entities.Pumpkin and can_harvest()):
		if get_entity_type() == Entities.Dead_Pumpkin:
			plant(Entities.Pumpkin)
			soak()
	k = get_tick_count()
	for i in range(100):
		tile(PUMPKIN)
	quick_print("OPS: tile(PUMPKIN) on a grown pumpkin", (get_tick_count() - k) / 100, "ticks")
	k = get_tick_count()
	for i in range(20):
		move(North)
	quick_print("OPS: move", (get_tick_count() - k) / 20, "ticks")
	t = get_time()
	k = get_tick_count()
	for i in range(20):
		move(North)
	quick_print("OPS: ticks per second while moving:", (get_tick_count() - k) / (get_time() - t))


# ---------- run everything ----------
# (earlier experiments already measured; uncomment to rerun)
quick_print("===== LAB =====")
lab_ops()
quick_print("===== LAB DONE =====")
