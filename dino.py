# ===== dino: Snake! Grow a dinosaur tail across the whole farm for bones =====
#
# The drone follows one big loop that visits every square and comes back
# to the start:
#   up the first column, then zig-zag left/right across the other columns
#   back down to the bottom, then one step West to the start.
# Because it's a single loop, the head can never run into the tail, so the
# snake always grows to fill the whole farm. Bones = tail length squared.

def next_dir(x, y, n):
	if x == 0:
		if y < n - 1:
			return North     # up the first column
		return East
	if (n - 1 - y) % 2 == 0:
		if x < n - 1:
			return East      # this row goes right
		return South
	if x > 1:
		return West          # this row goes left
	if y > 0:
		return South
	return West              # back to the start

def other_hat():
	for h in Hats:
		if h != Hats.Dinosaur_Hat and num_unlocked(h) > 0:
			return h
	return None

def apple_cost():
	return get_cost(Entities.Apple)

def do_dino():
	n = get_world_size()
	clear()                  # empty farm (apples only appear on empty tiles)
	change_hat(Hats.Dinosaur_Hat)
	# stop when the snake fills the farm (move fails), or when we've gone a
	# whole lap without seeing an apple (ran out of cactus)
	idle = 0
	while idle < n * n:
		if get_entity_type() == Entities.Apple:
			idle = 0
		else:
			idle += 1
		if not move(next_dir(get_pos_x(), get_pos_y(), n)):
			break
	# taking the hat off harvests the tail
	h = other_hat()
	if h != None:
		change_hat(h)
