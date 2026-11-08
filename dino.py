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

def loop_order(n):
	# square -> its position along the loop
	order = dict()
	x = 0
	y = 0
	for i in range(n * n):
		order[(x, y)] = i
		dx, dy = step[next_dir(x, y, n)]
		x += dx
		y += dy
	return order

def other_hat():
	for h in Hats:
		if h != Hats.Dinosaur_Hat and num_unlocked(h) > 0:
			return h
	return None

def apple_cost():
	return get_cost(Entities.Apple)


def pick_move(order, n, head, body, length, apple):
	# returns the best direction, or None to just follow the loop
	total = n * n
	if apple == None or length >= total * SNAKE_SHORTCUT_UNTIL:
		return None
	h = order[head]
	if length > 0:
		room = (order[body[len(body) - length]] - h) % total   # distance to tail
	else:
		room = total
	to_apple = (order[apple] - h) % total
	best = None
	best_gain = 1      # following the loop gains 1; only beat that
	for d in step:
		dx, dy = step[d]
		nb = (head[0] + dx, head[1] + dy)
		if nb[0] < 0 or nb[0] >= n or nb[1] < 0 or nb[1] >= n:
			continue
		gain = (order[nb] - h) % total
		# must stay ahead of the tail (with a little slack) and not overshoot
		if gain > best_gain and gain < room - 2 and gain <= to_apple:
			best = d
			best_gain = gain
	return best

def do_dino():
	n = get_world_size()
	clear()                  # empty farm (apples only appear on empty tiles)
	change_hat(Hats.Dinosaur_Hat)
	order = loop_order(n)
	body = []                # squares the head has left, oldest first
	length = 0               # tail segments (one per apple eaten)
	apple = None             # where the next apple will be
	idle = 0
	while idle < n * n:
		head = (get_pos_x(), get_pos_y())
		eating = get_entity_type() == Entities.Apple
		if eating:
			apple = measure()        # standing on an apple: where's the next one?
			idle = 0
		else:
			idle += 1

		d = pick_move(order, n, head, body, length, apple)
		if d == None or not move(d):
			if not move(next_dir(head[0], head[1], n)):
				break                # can't move: the snake fills the farm
		body.append(head)
		if eating:
			length += 1
		# forget squares the tail has already left (keeps the list short)
		if len(body) > length + 1:
			body.pop(0)

	# taking the hat off harvests the tail
	h = other_hat()
	if h != None:
		change_hat(h)
