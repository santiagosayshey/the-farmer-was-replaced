# ===== crops: what to do on a single tile =====

from config import HAY, WOOD, FERT, CARROT, BIG_CROP
from util import water


# ---------- normal farming ----------
# returns True when the tile is "ready" (only matters for big crops)

def tile(mode):
	if mode == HAY:
		if can_harvest():
			harvest()
		if get_ground_type() == Grounds.Soil and get_entity_type() == None:
			till()
		return True

	if mode == WOOD or mode == FERT:
		if can_harvest():
			harvest()
		e = get_entity_type()
		if e == None or e == Entities.Grass:
			if (get_pos_x() + get_pos_y()) % 2 == 0:
				plant(Entities.Tree)
			else:
				plant(Entities.Bush)
			if mode == FERT and num_items(Items.Fertilizer) > 0:
				use_item(Items.Fertilizer)
		water()
		return True

	if mode == CARROT:
		if can_harvest():
			harvest()
		e = get_entity_type()
		if e == None or e == Entities.Grass:
			if get_ground_type() != Grounds.Soil:
				till()
			plant(Entities.Carrot)
		water()
		return True

	# big crops: pumpkin, cactus, sunflower
	# (water only when planting: drones revisit these tiles constantly, and
	# topping up on every visit costs as much as a move)
	crop = BIG_CROP[mode]
	if get_entity_type() != crop:
		if can_harvest():
			harvest()
		if get_ground_type() != Grounds.Soil:
			till()
		plant(crop)
		water()
		return False
	return can_harvest()


# ---------- polyculture ----------
# Each plant wants a companion nearby. When we plant something, we ask what
# it wants and where, and write it down in `wants`. When we later reach that
# tile, we plant the companion instead of the normal crop.

def default_crop(mode):
	if mode == HAY:
		return Entities.Grass
	if mode == CARROT:
		return Entities.Carrot
	if (get_pos_x() + get_pos_y()) % 2 == 0:
		return Entities.Tree
	return Entities.Bush

def plant_crop(crop):
	if crop == Entities.Carrot:
		if get_ground_type() != Grounds.Soil:
			till()
	elif crop == Entities.Grass:
		if get_ground_type() == Grounds.Soil:
			till()
	plant(crop)

def poly_tile(mode, wants, new, done):
	# wants: the shared notebook (my copy)
	# new:   companion requests I found this round
	# done:  requests I fulfilled this round
	pos = (get_pos_x(), get_pos_y())
	if can_harvest():
		harvest()

	crop = default_crop(mode)
	requested = pos in wants
	if requested:
		crop = wants[pos]

	e = get_entity_type()
	if e == None or (e == Entities.Grass and crop != Entities.Grass):
		plant_crop(crop)
		if requested:
			wants.pop(pos)
			done.append(pos)

	# what does the plant here want? write it down, wherever it is
	comp = get_companion()
	if comp != None:
		want_type, want_pos = comp
		wants[want_pos] = want_type
		new[want_pos] = want_type
	water()
