# ===== util: small helpers everyone uses =====

def drones():
	# use every drone we have (more drones than columns is fine: columns
	# get split into pieces)
	k = max_drones()
	n = get_world_size()
	if k > n * n:
		k = n * n
	return k

def goto(x, y):
	while get_pos_x() != x:
		move(East)
	while get_pos_y() != y:
		move(North)

def goto_near(x, y):
	# shortest way there (the farm wraps around at the edges)
	n = get_world_size()
	dx = (x - get_pos_x() + n) % n
	if dx * 2 <= n:
		for s in range(dx):
			move(East)
	else:
		for s in range(n - dx):
			move(West)
	dy = (y - get_pos_y() + n) % n
	if dy * 2 <= n:
		for s in range(dy):
			move(North)
	else:
		for s in range(n - dy):
			move(South)

def water():
	if get_water() < 0.8 and num_items(Items.Water) > 50:
		use_item(Items.Water)
