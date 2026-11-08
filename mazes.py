# ===== mazes: one maze, reused many times, with drones guarding zones =====
#
# 1. Build one maze.
# 2. The drones map it together (splitting up at forks), merge the pieces
#    into one map, and everyone gets a copy.
# 3. The field is split into zones, one per drone. Each drone parks in the
#    middle of its zone.
# 4. measure() tells everyone where the treasure is. Only the drone whose
#    zone it's in goes for it, using the shortest path on its map.
# 5. At the treasure it uses Weird Substance: gold collected, treasure jumps
#    somewhere new, repeat. Walls disappear over time; drones notice new
#    openings as they walk and update their maps.
# 6. When we've spent enough substance (or hit the 300 reuse limit), the
#    treasure gets harvested, the maze vanishes, and everyone stops.

from config import MAZE_CYCLES
from util import drones

dirs = [North, East, South, West]
opposite = {North: South, East: West, South: North, West: East}
step = {North: (0, 1), East: (1, 0), South: (0, -1), West: (-1, 0)}


def maze_cost():
	return get_world_size() * 2 ** (num_unlocked(Unlocks.Mazes) - 1)

def make_maze(cost):
	clear()
	plant(Entities.Bush)
	while get_entity_type() == Entities.Bush:
		if can_harvest():
			use_item(Items.Weird_Substance, cost)
		elif num_items(Items.Fertilizer) > 0:
			use_item(Items.Fertilizer)
		else:
			do_a_flip()


# ---------- small helpers ----------

def here():
	return (get_pos_x(), get_pos_y())

def maze_over():
	e = get_entity_type()
	return e != Entities.Hedge and e != Entities.Treasure

def look(walls):
	open_dirs = []
	for d in dirs:
		if can_move(d):
			open_dirs.append(d)
	walls[here()] = open_dirs

def neighbour(pos, d):
	dx, dy = step[d]
	return (pos[0] + dx, pos[1] + dy)


# ---------- zones ----------

def grid(k):
	# split k drones into rows x cols of zones, as square as possible
	r = 1
	while (r + 1) * (r + 1) <= k:
		r += 1
	return [r, k // r]

def zone_of(p, k):
	if p == None:      # maze just ended, no treasure anywhere
		return -1
	n = get_world_size()
	g = grid(k)
	zx = p[0] * g[1] // n
	zy = p[1] * g[0] // n
	return zy * g[1] + zx

def zone_home(z, k):
	n = get_world_size()
	g = grid(k)
	zx = z % g[1]
	zy = z // g[1]
	x = (zx * n // g[1] + (zx + 1) * n // g[1] - 1) // 2
	y = (zy * n // g[0] + (zy + 1) * n // g[0] - 1) // 2
	return (x, y)


# ---------- mapping and paths ----------

def map_dfs(walls, helpers):
	# depth-first walk, writing down every wall. At a fork, if a drone is
	# free, hand it the side branch and keep mapping my own.
	# (Works because a fresh maze has no loops: branches never meet.)
	look(walls)
	pos = here()
	todo = []
	for d in walls[pos]:
		if not (neighbour(pos, d) in walls):
			todo.append(d)
	for j in range(len(todo)):
		d = todo[j]
		nb = neighbour(pos, d)
		if j < len(todo) - 1 and num_drones() < max_drones():
			h = spawn_drone(map_branch, d, pos)
			if h != None:
				walls[nb] = []      # placeholder: a helper is mapping this
				helpers.append(h)
				continue
		move(d)
		map_dfs(walls, helpers)
		move(opposite[d])

def merge(walls, other):
	# add another drone's map to mine (real entries beat placeholders)
	for pos in other:
		if not (pos in walls) or (len(walls[pos]) == 0 and len(other[pos]) > 0):
			walls[pos] = other[pos]

def map_branch(d, parent):
	walls = {parent: []}    # so I never walk back into my parent's area
	helpers = []
	move(d)
	map_dfs(walls, helpers)
	for h in helpers:
		merge(walls, wait_for(h))
	return walls

def map_maze():
	# everyone maps a piece; the pieces flow back up into one full map
	walls = dict()
	helpers = []
	map_dfs(walls, helpers)
	for h in helpers:
		merge(walls, wait_for(h))
	return walls

def path_to(walls, goal):
	# breadth-first search: the shortest list of moves to goal
	start = here()
	prev = {start: start}
	queue = [start]
	i = 0
	while i < len(queue):
		cur = queue[i]
		i += 1
		if cur == goal:
			break
		if cur in walls:
			for d in walls[cur]:
				nxt = neighbour(cur, d)
				if not (nxt in prev):
					prev[nxt] = (cur, d)
					queue.append(nxt)
	if not (goal in prev):
		return []
	moves = []
	cur = goal
	while cur != start:
		back, d = prev[cur]
		moves.append(d)
		cur = back
	return moves

def walk(walls, goal, zones, k, chasing):
	# follow the shortest path, but stop early if the situation changes
	moves = path_to(walls, goal)
	for i in range(len(moves) - 1, -1, -1):
		if maze_over():
			return
		if not move(moves[i]):
			look(walls)   # map was wrong here; fix it and re-plan
			return
		look(walls)       # spot walls that have disappeared
		t = measure()
		if t == None:
			return        # maze just ended
		if chasing and t != goal:
			return        # treasure moved, re-plan
		if not chasing and zone_of(t, k) in zones:
			return        # treasure showed up in my zone, go get it


# ---------- at the treasure ----------

def collect(stop_sub, cost):
	if get_entity_type() != Entities.Treasure:
		return
	sub = num_items(Items.Weird_Substance)
	if sub < cost or sub - cost < stop_sub:
		harvest()    # spent enough: finish the maze
		return
	t = here()
	# use substance; the treasure should jump somewhere else.
	# It can land on the same square by chance, so try twice. If it still
	# hasn't moved, we've hit the 300-reuse limit, so finish the maze.
	for attempt in range(2):
		if num_items(Items.Weird_Substance) < cost:
			harvest()
			return
		use_item(Items.Weird_Substance, cost)
		start = get_tick_count()
		while measure() == t and get_tick_count() - start < 2000:
			pass
		if measure() != t:
			return
	if get_entity_type() == Entities.Treasure:
		harvest()


# ---------- what every drone runs ----------

def worker(zones, k, stop_sub, cost, walls):
	home = zone_home(zones[0], k)
	while not maze_over():
		t = measure()
		if t == None:      # someone finished the maze a moment ago
			return
		if zone_of(t, k) in zones:
			if here() == t:
				collect(stop_sub, cost)
			else:
				walk(walls, t, zones, k, True)
		elif here() != home:
			walk(walls, home, zones, k, False)


def do_mazes():
	cost = maze_cost()
	if num_items(Items.Weird_Substance) < cost:
		return
	make_maze(cost)

	k = drones()
	g = grid(k)
	nzones = g[0] * g[1]
	stop_sub = num_items(Items.Weird_Substance) - cost * MAZE_CYCLES
	if stop_sub < 0:
		stop_sub = 0

	# map the maze together, then give everyone a copy
	walls = map_maze()

	# one zone per helper; any zone whose helper didn't spawn is mine
	mine = []
	for i in range(nzones - 1):
		if spawn_drone(worker, [i], k, stop_sub, cost, walls) == None:
			mine.append(i)
	mine.insert(0, nzones - 1)
	worker(mine, k, stop_sub, cost, walls)

	# wait for every helper to notice the maze is gone
	while num_drones() > 1:
		pass
