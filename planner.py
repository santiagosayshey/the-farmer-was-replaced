# ===== planner: decides what to farm next =====
#
# 1. It measures how many seconds of farming each item really costs
#    (including the inputs: a pumpkin costs pumpkin-time PLUS carrot-time).
# 2. For every upgrade in VALUE it asks:
#       payback = seconds to afford it / seconds it will save
#    where "seconds saved" = how much faster we could pay for ALL the
#    unlocks still ahead of us, if we had that upgrade.
# 3. It goes for the best payback. Cheap fluff gets bought on the way.
# 4. If it can afford something but unlock() fails, that unlock is locked
#    behind something else, so it's skipped until the next successful unlock.

from config import MAZE, FERT, DINO, CROP, MODE_FOR, MODE_ITEM, MODELED, TRACKED
from config import DEFAULT_OWN, VALUE, UNLOCKS, FLUFF_MAX, FIELD_BUFFER, BIG_MODES
from mazes import maze_cost
from dino import apple_cost

own = dict(DEFAULT_OWN)   # item -> seconds of farming per item (own work only)
inp = dict()              # item -> {input item: how many used per item made}
acc = dict()              # mode -> [seconds, gained, {item: used}] while measuring
blocked = set()           # unlocks that failed even though we could afford them
last_goal = [None, -1]    # [target, payback] for the status line


# ---------- cost model ----------

def init_inputs():
	for item in CROP:
		if item in MODELED:
			inp[item] = dict(get_cost(CROP[item]))
	n = get_world_size()
	inp[Items.Gold] = {Items.Weird_Substance: 1.0 / n}
	apple = apple_cost()
	mult = 2 ** (num_unlocked(Unlocks.Dinosaurs) - 1)
	bone = dict()
	for c in apple:
		bone[c] = apple[c] * 1.0 / (n * n * mult)
	inp[Items.Bone] = bone

def secs(item, boost, depth):
	# seconds to make 1 item, including making its inputs.
	# boost = {item: times faster} to test "what if I had this upgrade?"
	if depth > 6:
		return 0
	if item == Items.Bone and num_unlocked(Unlocks.Dinosaurs) == 0:
		big = 1000000
		if item in boost:
			big = big / boost[item]
		return big
	total = 0
	if item in own:
		total = own[item]
	if item in inp:
		ins = inp[item]
		for c in ins:
			total += ins[c] * secs(c, boost, depth + 1)
	if item in boost:
		total = total / boost[item]
	return total

def table(boost):
	t = dict()
	for item in MODELED:
		t[item] = secs(item, boost, 0)
	return t

def usable_cost(u):
	# the cost dict, or None if maxed out / needs items we can't make
	cost = get_cost(u)
	if len(cost) == 0:
		return None
	for item in cost:
		if not (item in MODELED):
			return None
	return cost


# ---------- measuring real rates ----------

def snapshot():
	s = dict()
	for item in TRACKED:
		s[item] = num_items(item)
	return s

def record(mode, before, t0, finished):
	item = MODE_ITEM[mode]
	if not (mode in acc):
		acc[mode] = [0, 0, dict()]
	a = acc[mode]
	a[0] += get_time() - t0
	a[1] += num_items(item) - before[item]
	used = a[2]
	for c in MODELED:
		if c != item:
			d = before[c] - num_items(c)
			if d > 0:
				if c in used:
					used[c] += d
				else:
					used[c] = d

	# big crops only pay out at the end, so wait until they finish
	if a[1] <= 0 or (mode in BIG_MODES and not finished):
		return

	# blend the new measurement 50/50 with what we knew
	new_own = a[0] / a[1]
	if item in own:
		own[item] = (own[item] + new_own) / 2
	else:
		own[item] = new_own
	old = dict()
	if item in inp:
		old = inp[item]
	merged = dict()
	for c in old:
		merged[c] = old[c] / 2
	for c in used:
		if c in merged:
			merged[c] += used[c] / a[1] / 2
		else:
			merged[c] = used[c] / a[1] / 2
	inp[item] = merged
	acc[mode] = [0, 0, dict()]


# ---------- choosing a target ----------

def unblock_all():
	for b in list(blocked):
		blocked.remove(b)

def worst_item(cost, base):
	# the missing item that will take the longest to farm
	best = None
	best_t = 0
	for item in cost:
		t = (cost[item] - num_items(item)) * base[item]
		if t > best_t:
			best = item
			best_t = t
	return best

def choose():
	# returns (target unlock, item to farm)
	if len(inp) == 0:
		init_inputs()

	if num_unlocked(Unlocks.Auto_Unlock) == 0:
		cost = get_cost(Unlocks.Auto_Unlock)
		if num_items(Items.Pumpkin) >= cost[Items.Pumpkin]:
			quick_print("You can buy Auto_Unlock now!")
		last_goal[0] = Unlocks.Auto_Unlock
		return (Unlocks.Auto_Unlock, Items.Pumpkin)

	base = table(dict())

	# buy what we can, and collect everything still ahead of us
	ahead = dict()     # unlock -> cost
	basket = dict()    # item -> total still missing across all of them
	for u in UNLOCKS:
		if u in blocked:
			continue
		cost = usable_cost(u)
		if cost == None:
			continue
		affordable = True
		spend = 0
		for item in cost:
			if num_items(item) < cost[item]:
				affordable = False
			spend += cost[item] * base[item]
		if affordable:
			if (u in VALUE) or spend < FLUFF_MAX:
				if unlock(u):
					quick_print("Unlocked:", u)
					unblock_all()
				else:
					blocked.add(u)
			continue
		ahead[u] = cost
		for item in cost:
			m = cost[item] - num_items(item)
			if m > 0:
				if item in basket:
					basket[item] += m
				else:
					basket[item] = m

	# best payback among upgrades; cheapest anything as a fallback
	best = None
	best_p = -1
	cheapest = None
	cheapest_t = -1
	for u in ahead:
		cost = ahead[u]
		t = 0
		for item in cost:
			m = cost[item] - num_items(item)
			if m > 0:
				t += m * base[item]
		if cheapest_t < 0 or t < cheapest_t:
			cheapest = u
			cheapest_t = t
		if u in VALUE:
			value = VALUE[u]
			if u == Unlocks.Dinosaurs and num_unlocked(Unlocks.Dinosaurs) > 0:
				value = {Items.Bone: 2}    # each level doubles bones
			boosted = table(value)
			saved = 0
			for item in basket:
				saved += basket[item] * (base[item] - boosted[item])
			if saved > 0:
				p = t / saved
				if best_p < 0 or p < best_p:
					best = u
					best_p = p

	target = best
	if target == None:
		target = cheapest
	if target == None:
		return (None, None)
	last_goal[0] = target
	last_goal[1] = best_p
	return (target, worst_item(ahead[target], base))


# ---------- which crop gets us an item ----------

def plan(item):
	# which mode gets us this item, growing its inputs first if we're short
	if item == Items.Gold:
		if num_items(Items.Weird_Substance) >= maze_cost():
			return MAZE
		return FERT
	if item == Items.Weird_Substance:
		return FERT
	if item == Items.Bone:
		n = get_world_size()
		apple = apple_cost()
		for c in apple:
			if num_items(c) < apple[c] * n * n * FIELD_BUFFER:
				return plan(c)
		return DINO
	if item in CROP:
		n = get_world_size()
		cost = get_cost(CROP[item])
		for c in cost:
			if num_items(c) < cost[c] * n * n * FIELD_BUFFER:
				return plan(c)
	return MODE_FOR[item]
