# ===== jobs: what each drone does, and running drones together =====

from config import PUMPKIN, CACTUS, SUN, POLY_MODES, PUMPKIN_ROUND_SECONDS, PUMPKIN_PATIENCE, PUMPKIN_GAP, PUMPKIN_PAIRS, PUMPKIN_BLOCK, PUMPKIN_LOOP
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
# for the WHOLE farm to merge, each drone owns some blocks (PUMPKIN_BLOCK
# wide, 6 or more), keeps them replanted, and harvests each block the
# moment it has merged.

BLOCK = PUMPKIN_BLOCK

def columns(a, b):
	# [a, a+1, ..., b-1]
	out = []
	for c in range(a, b):
		out.append(c)
	return out

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

def step_to(x, y):
	# walk inside a block (no wrapping around the farm)
	while get_pos_x() < x:
		move(East)
	while get_pos_x() > x:
		move(West)
	while get_pos_y() < y:
		move(North)
	while get_pos_y() > y:
		move(South)

def help_partner(x0, y0, cols):
	# My half is done but the block hasn't merged: the partner is still
	# waiting on dead pumpkins. Walk its columns, starting from the far side
	# (so we work towards each other), and replant dead ones.
	# Only dead ones: an empty tile may be one the partner hasn't planted
	# yet, and a grown one would get harvested as a single piece.
	other = []
	if cols[0] == 0:
		for c in range(BLOCK - 1, len(cols) - 1, -1):
			other.append(c)
	else:
		for c in range(cols[0]):
			other.append(c)
	for k in range(len(other)):
		for s in range(BLOCK):
			y = y0 + s
			if k % 2 == 1:
				y = y0 + BLOCK - 1 - s
			step_to(x0 + other[k], y)
			if get_entity_type() == Entities.Dead_Pumpkin:
				tile(PUMPKIN)

def do_block(x0, y0, deadline, patience, cols, tm):
	# cols: which columns of the block are mine (all 6, or one half when two
	# drones share a block)
	# tm: timing notebook (seconds spent planting / on dead pumpkins)
	t0 = get_time()
	goto(x0 + cols[0], y0)
	# 1. one zig-zag over my columns. Harvest anything that's grown (pieces
	#    left over from last time), plant / replant everything, and write
	#    down every tile that isn't ready yet (the to-do list).
	#    Harvesting here means pieces never need a separate pass.
	todo = []
	for c in range(len(cols)):
		for s in range(BLOCK):
			if get_entity_type() == Entities.Pumpkin and can_harvest():
				harvest()
			if not tile(PUMPKIN):
				todo.append((get_pos_x(), get_pos_y()))
			if s < BLOCK - 1:
				if c % 2 == 0:
					move(North)
				else:
					move(South)
		if c < len(cols) - 1:
			move(East)
	t1 = get_time()
	tm["t_plant"] += t1 - t0

	# 2. only revisit the to-do tiles (a grown, live pumpkin stays that way,
	#    so the list only ever shrinks, apart from dead ones being replanted)
	while len(todo) > 0:
		if get_time() >= deadline:
			tm["t_dead"] += get_time() - t1
			return "unfinished"
		left = []
		for p in todo:
			step_to(p[0], p[1])
			if get_entity_type() == Entities.Dead_Pumpkin:
				tm["dead"] += 1
			if not tile(PUMPKIN):
				left.append(p)
		todo = left
	tm["t_dead"] += get_time() - t1

	# 3. my tiles are all grown and alive: is the whole block one giant
	#    pumpkin? (bottom corners have the same measure() number).
	#    Sharing a block: keep waiting for the partner's half (with gaps,
	#    blocks reliably merge), but if a corner is empty or dead, the
	#    partner already harvested it: go back and replant.
	#    Alone: if it stays in pieces, leave them for the next zig-zag.
	tries = patience + 1
	if len(cols) < BLOCK:
		tries = 100000
	for attempt in range(tries):
		if attempt > 0 and len(cols) < BLOCK:
			help_partner(x0, y0, cols)
		step_to(x0 + BLOCK - 1, y0)
		a = measure()
		for s in range(BLOCK - 1):
			move(West)
		b = measure()
		# a = bottom-right corner, b = bottom-left corner
		mine = b
		if cols[0] > 0:
			mine = a
		if len(cols) < BLOCK:
			if mine == None:
				return "partner"     # my half was emptied: partner harvested
			if a == None or b == None:
				if get_time() >= deadline:
					return "unfinished"
				continue             # partner's corner is dead/empty: wait
		elif a == None or b == None:
			return "partner"
		if a == b and can_harvest():
			harvest()     # the whole 6x6 giant: best case
			return "merged"
		if get_time() >= deadline:
			return "unfinished"
	return "pieces"

def loop_cells():
	# a closed loop through every tile of a 6x6 block:
	# up column 0, zig-zag columns 1-5 in rows 1-5, back along row 0
	cells = []
	for y in range(6):
		cells.append([0, y])
	for c in range(1, 6):
		if c % 2 == 1:
			for y in range(5, 0, -1):
				cells.append([c, y])
		else:
			for y in range(1, 6):
				cells.append([c, y])
	for x in range(5, 0, -1):
		cells.append([x, 0])
	return cells

def loop_dirs(cells):
	dirs = []
	for j in range(len(cells)):
		a = cells[j]
		b = cells[(j + 1) % len(cells)]
		if b[0] > a[0]:
			dirs.append(East)
		elif b[0] < a[0]:
			dirs.append(West)
		elif b[1] > a[1]:
			dirs.append(North)
		else:
			dirs.append(South)
	return dirs

def loop_block(x0, y0, deadline, start):
	# Two drones go round the same loop, half a lap apart, until the round
	# ends. Half a lap is always longer than a watered pumpkin takes to
	# grow, so every visit finds a finished tile: plant anything empty or
	# dead, and at the two bottom corners check whether the block merged
	# (same measure() number at both = one 6x6 giant) and harvest it.
	cells = loop_cells()
	dirs = loop_dirs(cells)
	j = start
	goto(x0 + cells[j][0], y0 + cells[j][1])
	corner = {0: None, 5: None}
	merged = 0
	jumps = 0
	while get_time() < deadline:
		c = cells[j]
		e = get_entity_type()
		if e == Entities.Pumpkin and not can_harvest():
			# still growing = the partner planted it moments ago: I've caught
			# up (bus bunching). Jump half a lap ahead to spread out again;
			# the loop folds, so that's only a few tiles away.
			j = (j + len(cells) // 2) % len(cells)
			step_to(x0 + cells[j][0], y0 + cells[j][1])
			jumps += 1
			continue
		if e != Entities.Pumpkin:
			tile(PUMPKIN)
		elif c[1] == 0 and (c[0] == 0 or c[0] == 5):
			m = measure()
			if m != None and m == corner[5 - c[0]] and can_harvest():
				harvest()
				merged += 1
				corner = {0: None, 5: None}
			else:
				corner[c[0]] = m
		move(dirs[j])
		j = (j + 1) % len(cells)
	return [merged, jumps]

def pumpkin_job(arg, i, k):
	# Everyone works until the shared game clock passes the deadline, so
	# nobody waits around for an unlucky block. Unfinished blocks simply
	# carry on next round (the pumpkins are still in the ground).
	# gap > 0: blocks are separated by strips of grass, so giant pumpkins
	# can't form across two blocks.
	deadline = arg[0]
	patience = arg[1]
	gap = arg[2]
	n = get_world_size()
	span = BLOCK + gap
	per = (n + gap) // span
	blocks = per * per
	counts = {"merged": 0, "pieces": 0, "unfinished": 0, "strip": 0, "partner": 0}
	# timing (drone-seconds): t_block = everything inside blocks; the part
	# that isn't planting or dead pumpkins is corner checks / waiting / harvest
	tm = {"t_plant": 0, "t_dead": 0, "t_block": 0, "dead": 0}
	# enough drones for two per block? then each takes half the columns
	# (an odd width gives the second drone the extra column)
	pairs = PUMPKIN_PAIRS and blocks > 0 and k >= 2 * blocks
	if pairs and i < 2 * blocks and PUMPKIN_LOOP and BLOCK == 6 and gap > 0:
		b = i // 2
		r = loop_block((b % per) * span, (b // per) * span, deadline, (i % 2) * 18)
		counts["merged"] += r[0]
		counts["jumps"] = r[1]
		return counts
	if pairs and i < 2 * blocks:
		b = i // 2
		if i % 2 == 0:
			cols = columns(0, BLOCK // 2)
		else:
			cols = columns(BLOCK // 2, BLOCK)
		while get_time() < deadline:
			t = get_time()
			counts[do_block((b % per) * span, (b // per) * span, deadline, patience, cols, tm)] += 1
			tm["t_block"] += get_time() - t
		for name in tm:
			counts[name] = tm[name]
		return counts
	if not pairs and i < blocks:
		while get_time() < deadline:
			b = i
			while b < blocks and get_time() < deadline:
				t = get_time()
				counts[do_block((b % per) * span, (b // per) * span, deadline, patience, columns(0, BLOCK), tm)] += 1
				tm["t_block"] += get_time() - t
				b += k
		for name in tm:
			counts[name] = tm[name]
		return counts
	# spare drones: every tile that isn't inside a block
	busy = blocks
	if pairs:
		busy = 2 * blocks
	spares = k - busy
	if spares <= 0:
		return counts
	j = i - busy
	mine = []
	count = 0
	for x in range(n):
		for y in range(n):
			inside = x // span < per and y // span < per and x % span < BLOCK and y % span < BLOCK
			if not inside:
				if count % spares == j:
					mine.append((x, y))
				count += 1
	if gap > 0:
		# keep the gaps (and leftover edges) as grass: clear anything else
		# off them and turn soil back into grassland. Grass regrows by itself.
		for p in mine:
			goto(p[0], p[1])
			e = get_entity_type()
			if e != None and e != Entities.Grass:
				harvest()
			if get_ground_type() == Grounds.Soil:
				till()
		return counts
	# no gaps: grow pumpkins on the leftover strip too
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

def pumpkin_round(seconds, patience, gap):
	# one timed pumpkin round; counts go into `extra`
	for counts in fork_all(pumpkin_job, [get_time() + seconds, patience, gap]):
		for name in counts:
			if name in extra:
				extra[name] += counts[name]
			else:
				extra[name] = counts[name]

def field_round(mode, wants):
	for name in list(extra):
		extra.pop(name)

	if mode in POLY_MODES and num_unlocked(Unlocks.Polyculture) > 0:
		fork_poly(mode, wants)
		extra["requests open"] = len(wants)
		return True

	if mode == PUMPKIN and get_world_size() >= BLOCK:
		pumpkin_round(PUMPKIN_ROUND_SECONDS, PUMPKIN_PATIENCE, PUMPKIN_GAP)
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
