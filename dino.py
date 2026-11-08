# ===== dino: Snake! Grow a dinosaur tail across the whole farm for bones =====
#
# Safe loop: up the first column, then zig-zag left/right across the other
# columns back down to the bottom, then one step West to the start. Following
# it can never hit the tail.
#
# Shortcuts: number every square by its place on the loop. The body always
# sits in the stretch of loop between tail and head, so every square AHEAD
# of the head (up to the tail) is empty. While the snake is short, the head
# may jump to any neighbour further ahead on the loop, as long as it doesn't
# pass its own tail or overshoot the apple. When the snake gets long, it
# stops cutting corners and just follows the loop.
#
# Speed: once the snake has eaten ~80 apples, moves are so cheap that the
# THINKING is half the cost. So everything is worked out once up front
# (tables), and each step does as little as possible.
#
# Bones = tail length squared.

from config import SNAKE_SHORTCUT_UNTIL

step = {North: (0, 1), East: (1, 0), South: (0, -1), West: (-1, 0)}


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

def build_tables(n):
	# order[sq]  = place on the loop
	# follow[sq] = [direction, next square] along the loop
	# jumps[sq]  = [[direction, neighbour, its place], ...] for every neighbour
	order = dict()
	follow = dict()
	x = 0
	y = 0
	for i in range(n * n):
		d = next_dir(x, y, n)
		dx, dy = step[d]
		order[(x, y)] = i
		follow[(x, y)] = [d, (x + dx, y + dy)]
		x += dx
		y += dy
	jumps = dict()
	for sq in order:
		options = []
		for d in step:
			dx, dy = step[d]
			nb = (sq[0] + dx, sq[1] + dy)
			if nb in order:
				options.append([d, nb, order[nb]])
		jumps[sq] = options
	return [order, follow, jumps]

def other_hat():
	for h in Hats:
		if h != Hats.Dinosaur_Hat and num_unlocked(h) > 0:
			return h
	return None

def apple_cost():
	return get_cost(Entities.Apple)


def do_dino():
	n = get_world_size()
	total = n * n
	clear()                  # empty farm (apples only appear on empty tiles)
	tables = build_tables(n)
	order = tables[0]
	follow = tables[1]
	jumps = tables[2]
	cut_off = total * SNAKE_SHORTCUT_UNTIL
	t0 = get_time()

	change_hat(Hats.Dinosaur_Hat)
	head = (0, 0)            # clear() puts us at (0, 0)
	body = []                # every square the head has left (never shrinks)
	length = 0               # tail segments = apples eaten
	apple_at = -1            # loop place of the next apple (-1 = unknown)
	idle = 0
	while idle < total and length < cut_off:
		h = order[head]
		eating = get_entity_type() == Entities.Apple
		if eating:
			a = measure()    # standing on an apple: where's the next one?
			if a == None:
				apple_at = -1
			else:
				apple_at = order[a]
			idle = 0
		else:
			idle += 1

		# default: follow the loop
		nxt = follow[head]
		d = nxt[0]
		target = nxt[1]

		# shortcut: furthest jump that stays behind the tail and the apple
		if length < cut_off and apple_at >= 0:
			if length > 0:
				room = (order[body[len(body) - length]] - h) % total - 2
			else:
				room = total
			reach = (apple_at - h) % total
			if room < reach:
				reach = room
			best = 1
			for option in jumps[head]:
				gain = (option[2] - h) % total
				if gain > best and gain <= reach:
					best = gain
					d = option[0]
					target = option[1]

		if not move(d):
			if d == nxt[0] or not move(nxt[0]):
				break        # can't move: the snake fills the farm
			target = nxt[1]
		body.append(head)
		head = target
		if eating:
			length += 1

	t_cut = get_time()
	# Long snake: just follow the loop. No apple or tail tracking needed, so
	# this loop is tiny (moves are cheap now; thinking would be the cost).
	# Every lap, check we can still afford apples, so we don't loop forever.
	if idle < total:
		cost = apple_cost()
		steps = 0
		while move(follow[head][0]):
			head = follow[head][1]
			steps += 1
			if steps >= total:
				steps = 0
				for c in cost:
					if num_items(c) < cost[c]:
						idle = total
				if idle >= total:
					break

	t_end = get_time()
	# taking the hat off harvests the tail
	h = other_hat()
	if h != None:
		change_hat(h)
	return {"snakes": 1, "shortcut seconds": t_cut - t0, "loop seconds": t_end - t_cut}
