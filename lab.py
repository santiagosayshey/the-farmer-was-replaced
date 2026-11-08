# ===== lab: measure the game's real rules =====
# Run this INSIDE simulate() (see the lab_sim window) so the real farm isn't
# touched: set_world_size() clears the farm. Each experiment prints results
# to the output window. Send the output back so the simulations can be
# calibrated against the real game.

from dino import other_hat

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


# ---------- run everything ----------
quick_print("===== LAB =====")
lab_speed()
lab_pumpkins(15, False)
lab_pumpkins(15, True)
lab_trees()
lab_snake_plants()
quick_print("===== LAB DONE =====")
