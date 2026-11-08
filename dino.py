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


def do_dino(cut, light):
	# cut = share of the farm to keep cutting corners until (< 0: use config)
	# light = check shortcuts with can_move() instead of tracking the tail
	#         (much less thinking per step; a tip from the game's Discord)
	n = get_world_size()
	total = n * n
	clear()                  # empty farm (apples only appear on empty tiles)
	tables = build_tables(n)
	order = tables[0]
	follow = tables[1]
	jumps = tables[2]
	if cut < 0:
		cut = SNAKE_SHORTCUT_UNTIL
	cut_off = total * cut
	t0 = get_time()

	# lean tables on loop places (plain numbers, not (x, y) squares):
	#   ldir[i]  = direction from place i to place i + 1
	#   ljump[i] = [[gain, direction], ...] biggest gain first (gain 1 = follow)
	#   sq_at[i] = the square at place i
	ldir = []
	sq_at = []
	for i in range(total):
		ldir.append(None)
		sq_at.append(None)
	for sq in order:
		ldir[order[sq]] = follow[sq][0]
		sq_at[order[sq]] = sq
	ljump = []
	for i in range(total):
		opts = []
		for option in jumps[sq_at[i]]:
			gain = (option[2] - i) % total
			if gain >= 1 and gain < total // 2:
				opts.append([gain, option[0]])
		# sort biggest first (tiny lists: insertion sort)
		for p in range(1, len(opts)):
			q = p
			while q > 0 and opts[q][0] > opts[q - 1][0]:
				t = opts[q]
				opts[q] = opts[q - 1]
				opts[q - 1] = t
				q -= 1
		ljump.append(opts)

	change_hat(Hats.Dinosaur_Hat)
	h = 0                    # place on the loop; clear() puts us at (0, 0) = place 0
	hist = []                # every place the head has left (never shrinks)
	length = 0               # tail segments = apples eaten
	apple_at = -1            # place of the next apple (-1 = unknown)
	idle = 0
	if get_entity_type() == Entities.Apple:
		apple_at = 0
	follow1 = [1, None]
	while light and length < cut_off and idle < total:
		grow = 0
		if h == apple_at:
			a = measure()
			apple_at = -1
			if a != None:
				apple_at = order[a]
			grow = 1
			idle = 0
		elif apple_at < 0:
			idle += 1
			if get_entity_type() == Entities.Apple:
				apple_at = h
				continue
		reach = (apple_at - h) % total
		gain = 1
		d = ldir[h]
		for g in ljump[h]:
			if g[0] == 1:
				break
			if g[0] <= reach and can_move(g[1]):
				gain = g[0]
				d = g[1]
				break
		if not move(d):
			break            # boxed in (or the farm is full)
		h = (h + gain) % total
		length += grow
	while not light and length < cut_off and idle < total:
		grow = 0
		if h == apple_at:
			# standing on the apple: where's the next one?
			a = measure()
			apple_at = -1
			if a != None:
				apple_at = order[a]
			grow = 1
			idle = 0
		elif apple_at < 0:
			idle += 1
			if get_entity_type() == Entities.Apple:
				apple_at = h
				continue
		reach = (apple_at - h) % total
		if length > 0:
			room = (hist[len(hist) - length] - h) % total - 2
			if room < reach:
				reach = room
		pick = follow1
		for g in ljump[h]:
			if g[0] <= reach:
				pick = g
				break
		if pick[0] == 1 or not move(pick[1]):
			pick = follow1
			if not move(ldir[h]):
				break        # can't move: the snake fills the farm
		hist.append(h)
		h = (h + pick[0]) % total
		length += grow
	head = sq_at[h]
	body = hist

	t_cut = get_time()
	# Long snake: just follow the loop. No apple or tail tracking needed, so
	# this loop is tiny (moves are cheap now; thinking would be the cost).
	# Every lap, check we can still afford apples, so we don't loop forever.
	if idle < total:
		cost = apple_cost()
		# the loop as a plain list of directions, starting from the head, so
		# each step is just "move, did it work?" (two lines of code)
		lap = []
		sq = head
		for i in range(total):
			lap.append(follow[sq][0])
			sq = follow[sq][1]
		going = True
		while going:
			for d in lap:
				if not move(d):
					going = False
					break
			if going:
				for c in cost:
					if num_items(c) < cost[c]:
						going = False

	t_end = get_time()
	# taking the hat off harvests the tail
	h = other_hat()
	if h != None:
		change_hat(h)
	return {"snakes": 1, "shortcut seconds": t_cut - t0, "loop seconds": t_end - t_cut}
