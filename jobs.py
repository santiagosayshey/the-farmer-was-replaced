# ===== jobs: what each drone does, and running drones together =====

from config import PUMPKIN, CACTUS, SUN, POLY_MODES, PUMPKIN_ROUND_SECONDS
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

def walk_line(pos, target, fwd, back):
	while pos < target:
		move(fwd)
		pos += 1
	while pos > target:
		move(back)
		pos -= 1
	return pos

def sort_line(fwd, back, n):
	# Cocktail shaker sort with shrinking bounds, along one row or column.
	# Sweep forward (big cacti ride to the end), then backward (small ones
	# ride to the start). Everything past the last swap is already in order,
	# so the unsorted stretch [lo, hi] shrinks from both ends.
	pos = 0
	lo = 0
	hi = n - 1
	while lo < hi:
		pos = walk_line(pos, lo, fwd, back)
		last = lo
		for p in range(lo, hi):
			if measure() > measure(fwd):
				swap(fwd)
				last = p
			move(fwd)
		pos = hi
		hi = last
		if lo >= hi:
			break
		pos = walk_line(pos, hi, fwd, back)
		last = hi
		for p in range(hi, lo, -1):
			if measure() < measure(back):
				swap(back)
				last = p
			move(back)
		pos = lo
		lo = last

def sort_job(dir, i, k):
	# sort my rows (dir = East) or my columns (dir = North)
	n = get_world_size()
	line = i
	while line < n:
		if dir == East:
			goto(0, line)
			sort_line(East, West, n)
		else:
			goto(line, 0)
			sort_line(North, South, n)
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

def do_block(x0, y0, deadline):
	goto(x0, y0)
	stale = 0     # sweeps where everything was grown but not one pumpkin
	while get_time() < deadline:
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
				return "merged"
			# The game merges ANY fully grown square, so a block can end up
			# as several smaller giants that never join. Give it a couple
			# more sweeps, then take the pieces rather than wait forever.
			stale += 1
			if stale >= 2:
				harvest_block(x0, y0)
				return "pieces"
		goto(x0, y0)
	return "unfinished"

def pumpkin_job(deadline, i, k):
	# Everyone works until the shared game clock passes the deadline, so
	# nobody waits around for an unlucky block. Unfinished blocks simply
	# carry on next round (the pumpkins are still in the ground).
	n = get_world_size()
	per = n // BLOCK
	blocks = per * per
	counts = {"merged": 0, "pieces": 0, "unfinished": 0, "strip": 0}
	if i < blocks:
		while get_time() < deadline:
			b = i
			while b < blocks and get_time() < deadline:
				counts[do_block((b % per) * BLOCK, (b // per) * BLOCK, deadline)] += 1
				b += k
		return counts
	# spare drones: keep looping over the leftover strip along the top and
	# right edges
	spares = k - blocks
	j = i - blocks
	edge = per * BLOCK
	mine = []
	count = 0
	for x in range(n):
		for y in range(n):
			if x >= edge or y >= edge:
				if count % spares == j:
					mine.append((x, y))
				count += 1
	while get_time() < deadline and len(mine) > 0:
		for p in mine:
			if get_time() >= deadline:
				break
			goto(p[0], p[1])
			if tile(PUMPKIN):
				harvest()
				counts["strip"] += 1
	return counts


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

extra = dict()   # numbers from the last round, for stats

def field_round(mode, wants):
	for name in list(extra):
		extra.pop(name)

	if mode in POLY_MODES and num_unlocked(Unlocks.Polyculture) > 0:
		fork_poly(mode, wants)
		extra["requests open"] = len(wants)
		return True

	if mode == PUMPKIN and get_world_size() >= BLOCK:
		for counts in fork_all(pumpkin_job, get_time() + PUMPKIN_ROUND_SECONDS):
			for name in counts:
				if name in extra:
					extra[name] += counts[name]
				else:
					extra[name] = counts[name]
		return True

	ok = fork(field_job, mode)
	if not ok:
		return False
	if mode == PUMPKIN:
		harvest()
	elif mode == CACTUS:
		t = get_time()
		fork(sort_job, East)
		fork(sort_job, North)
		extra["sort seconds"] = get_time() - t
		extra["fields"] = 1
		harvest()
	elif mode == SUN:
		harvest_sunflowers()
	return True
