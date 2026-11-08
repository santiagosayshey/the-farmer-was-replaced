# ===== jobs: what each drone does, and running drones together =====

from config import PUMPKIN, CACTUS, SUN, POLY_MODES
from util import drones, goto
from crops import tile, poly_tile


# ---------- which tiles are mine ----------

def sweep(i, k, fn):
	# Visit every tile that drone i (of k) is in charge of, running fn() on
	# each one. fn() returns False if that tile isn't ready yet.
	#   k <= columns: drone i owns columns i, i+k, i+2k ...
	#   k >  columns: each column is split into pieces, one drone per piece
	n = get_world_size()
	ok = True
	if k <= n:
		c = i
		while c < n:
			for y in range(n):
				if not fn():
					ok = False
				move(North)
			c += k
			if c < n:          # only walk over if I have another column
				for s in range(k):
					move(East)
	else:
		pieces = k // n
		c = i % n
		p = i // n
		if p >= pieces:
			return True        # spare drone, nothing for me
		y0 = p * n // pieces
		y1 = (p + 1) * n // pieces
		goto(c, 0)
		# start from whichever end of my piece is closer (the field wraps)
		up = y0
		down = n - (y1 - 1)
		if down < up:
			for s in range(down):
				move(South)
			d = South
		else:
			for s in range(up):
				move(North)
			d = North
		for y in range(y1 - y0):
			if not fn():
				ok = False
			move(d)
	return ok


# ---------- drone jobs ----------

def field_job(mode, i, k):
	def work():
		return tile(mode)
	return sweep(i, k, work)

def poly_job(arg, i, k):
	mode = arg[0]
	wants = dict(arg[1])
	new = dict()
	done = []
	def work():
		poly_tile(mode, wants, new, done)
		return True
	sweep(i, k, work)
	return [new, done]

def petal_job(unused, i, k):
	found = []
	def work():
		found.append([measure(), get_pos_x(), get_pos_y()])
		return True
	sweep(i, k, work)
	return found

def sort_job(dir, i, k):
	# bubble sort my rows (dir = East) or my columns (dir = North)
	n = get_world_size()
	line = i
	while line < n:
		if dir == East:
			goto(0, line)
		else:
			goto(line, 0)
		swapped = True
		while swapped:
			swapped = False
			for s in range(n - 1):
				if measure() > measure(dir):
					swap(dir)
					swapped = True
				move(dir)
			move(dir)   # wraps back to the start of the line
		line += k
	return True

# ---------- pumpkins in 6x6 blocks ----------
# A 6x6 pumpkin already pays the most per tile (6), so instead of waiting
# for the WHOLE farm to merge, each drone owns some 6x6 blocks, keeps them
# replanted, and harvests each block the moment it has merged.

BLOCK = 6

def merged_here_and(d):
	# same "mysterious number" from measure() = same giant pumpkin
	a = measure()
	for s in range(BLOCK - 1):
		move(d)
	return a != None and a == measure() and can_harvest()

def harvest_block(x0, y0):
	# harvest whatever giants are in the block (pieces can be any size).
	# The first tile of each giant takes the whole thing; the rest are empty.
	goto(x0, y0)
	for col in range(BLOCK):
		for s in range(BLOCK):
			if can_harvest():
				harvest()
			if s < BLOCK - 1:
				if col % 2 == 0:
					move(North)
				else:
					move(South)
		if col < BLOCK - 1:
			move(East)

def do_block(x0, y0):
	goto(x0, y0)
	stale = 0     # sweeps where everything was grown but not one pumpkin
	while True:
		# sweep the block in a zig-zag, replanting anything dead or missing
		ready = True
		for col in range(BLOCK):
			for s in range(BLOCK):
				if not tile(PUMPKIN):
					ready = False
				if s < BLOCK - 1:
					if col % 2 == 0:
						move(North)
					else:
						move(South)
			if col < BLOCK - 1:
				move(East)
		# 6 columns up/down/up/down/up/down ends at the bottom-right corner.
		# If the bottom-right and bottom-left corners are the same pumpkin,
		# the block has merged.
		if ready:
			if merged_here_and(West):
				harvest()     # takes the whole 6x6 giant: best case
				return
			# The game merges ANY fully grown square, so a block can end up
			# as several smaller giants that never join. Give it a couple
			# more sweeps, then take the pieces rather than wait forever.
			stale += 1
			if stale >= 2:
				harvest_block(x0, y0)
				return
		goto(x0, y0)

def pumpkin_job(unused, i, k):
	n = get_world_size()
	per = n // BLOCK
	blocks = per * per
	if i < blocks:
		b = i
		while b < blocks:
			do_block((b % per) * BLOCK, (b // per) * BLOCK)
			b += k
		return True
	# spare drones: the leftover strip along the top and right edges
	spares = k - blocks
	j = i - blocks
	edge = per * BLOCK
	count = 0
	for x in range(n):
		for y in range(n):
			if x >= edge or y >= edge:
				if count % spares == j:
					goto(x, y)
					if tile(PUMPKIN) and can_harvest():
						harvest()
				count += 1
	return True


def harvest_job(points):
	for p in points:
		goto(p[0], p[1])
		harvest()
	return True


# ---------- running drones together (fork / join) ----------

def leader(job, arg, c, k):
	# column leader: spawn partners for the other pieces of my column,
	# do my own piece, then collect everyone's results
	n = get_world_size()
	ds = []
	for p in range(1, k // n):
		d = spawn_drone(job, arg, p * n + c, k)
		if d != None:
			ds.append(d)
	out = [job(arg, c, k)]
	for d in ds:
		out.append(wait_for(d))
	return out

def fork_all(job, arg):
	# spawn everyone, do my own share, return everyone's results
	k = drones()
	n = get_world_size()
	goto(0, 0)
	ds = []
	results = []
	if k <= n:
		for i in range(k - 1):
			d = spawn_drone(job, arg, i, k)
			if d != None:
				ds.append(d)
			move(East)
		results.append(job(arg, k - 1, k))
		for d in ds:
			results.append(wait_for(d))
	else:
		# one leader per column; leaders spawn their own partners
		for c in range(n - 1):
			d = spawn_drone(leader, job, arg, c, k)
			if d != None:
				ds.append(d)
			move(East)
		results = leader(job, arg, n - 1, k)
		for d in ds:
			for r in wait_for(d):
				results.append(r)
	return results

def fork(job, arg):
	ok = True
	for r in fork_all(job, arg):
		if not r:
			ok = False
	return ok

def fork_collect(job, arg):
	everything = []
	for r in fork_all(job, arg):
		for item in r:
			everything.append(item)
	return everything

def fork_poly(mode, wants):
	# everyone gets a copy of the shared notebook, then we merge their notes
	results = fork_all(poly_job, [mode, wants])
	# cross off requests that got planted
	for r in results:
		for pos in r[1]:
			if pos in wants:
				wants.pop(pos)
	# add the new requests
	for r in results:
		new = r[0]
		for pos in new:
			wants[pos] = new[pos]

def harvest_sunflowers():
	# biggest petals first, so (almost) every harvest gets the 8x bonus
	all_points = fork_collect(petal_job, 0)
	k = drones()
	for petals in range(15, 6, -1):
		chunks = []
		for i in range(k):
			chunks.append([])
		j = 0
		for p in all_points:
			if p[0] == petals:
				chunks[j % k].append([p[1], p[2]])
				j += 1
		ds = []
		for i in range(k - 1):
			if len(chunks[i]) > 0:
				d = spawn_drone(harvest_job, chunks[i])
				if d != None:
					ds.append(d)
		harvest_job(chunks[k - 1])
		for d in ds:
			wait_for(d)


# ---------- one round of farming ----------

def field_round(mode, wants):
	if mode in POLY_MODES and num_unlocked(Unlocks.Polyculture) > 0:
		fork_poly(mode, wants)
		return True

	if mode == PUMPKIN and get_world_size() >= BLOCK:
		fork(pumpkin_job, 0)   # every block harvested once
		return True

	ok = fork(field_job, mode)
	if not ok:
		return False
	if mode == PUMPKIN:
		harvest()
	elif mode == CACTUS:
		fork(sort_job, East)
		fork(sort_job, North)
		harvest()
	elif mode == SUN:
		harvest_sunflowers()
	return True
