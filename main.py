# ===== main: the loop. Run this one. =====

from config import MAZE, DINO, BIG_MODES, STUCK_LIMIT, POWER_MIN, REPLAN_EVERY
from config import MODE_ITEM
from jobs import field_round
from mazes import do_mazes
from dino import do_dino
from planner import choose, plan, record, snapshot, last_goal
from status import show

current = -1     # a big crop we're in the middle of (-1 = none)
stuck = 0
mode = -1
since_plan = REPLAN_EVERY   # forces a plan on the first round
wants = dict()   # shared polyculture notebook: position -> companion plant

while True:
	if current != -1 and stuck < STUCK_LIMIT:
		mode = current
	elif since_plan >= REPLAN_EVERY or mode == MAZE or mode == DINO or mode == -1:
		current = -1
		stuck = 0
		since_plan = 0
		target, item = choose()
		if item == None:
			item = Items.Pumpkin
		mode = plan(item)

	# Power is cheap to check, so do it every round
	run = mode
	if current == -1 and num_unlocked(Unlocks.Sunflowers) > 0 and num_items(Items.Power) < POWER_MIN:
		run = plan(Items.Power)

	show(last_goal[0], last_goal[1], MODE_ITEM[run], run)

	before = snapshot()
	t0 = get_time()
	since_plan += 1

	if run == MAZE:
		do_mazes()
		record(run, before, t0, True)
		continue
	if run == DINO:
		do_dino()
		record(run, before, t0, True)
		continue

	done = field_round(run, wants)
	record(run, before, t0, done)
	if run in BIG_MODES:
		if done:
			current = -1
			stuck = 0
			since_plan = REPLAN_EVERY   # big crop finished: re-plan now
		else:
			current = run
			stuck += 1
