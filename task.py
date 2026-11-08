# ===== task: what runs inside the sandbox or a leaderboard run =====
# Never press play here. The run window starts this through simulate()
# (practice) or leaderboard_run() (real). Which job: TASK in config.
# New experiments go in lab (or here), never in a new window.

from config import TASK, PUMPKIN_PATIENCE, PUMPKIN_GAP
from jobs import pumpkin_round
from dino import do_dino
import lab

def lb_pumpkins():
	goal = 200000000
	t0 = get_time()
	while num_items(Items.Pumpkin) < goal:
		pumpkin_round(3600, PUMPKIN_PATIENCE, PUMPKIN_GAP, goal)
	quick_print("LEADERBOARD pumpkins:", num_items(Items.Pumpkin), "in", get_time() - t0, "s")

def lb_dino():
	goal = 33488928
	t0 = get_time()
	while num_items(Items.Bone) < goal:
		do_dino(-1)
	quick_print("LEADERBOARD bones:", num_items(Items.Bone), "in", get_time() - t0, "s")

def snake_compare():
	# one full snake per cut-off (different random apples each time, so
	# only trust big differences)
	for cut in [0.05, 0.1, 0.15, 0.2]:
		b0 = num_items(Items.Bone)
		t0 = get_time()
		do_dino(cut)
		quick_print("SNAKE cut", cut, ":", get_time() - t0, "game seconds, bones", num_items(Items.Bone) - b0)

quick_print("===== TASK", TASK, "=====")
if TASK == "lb_pumpkins":
	lb_pumpkins()
elif TASK == "lb_dino":
	lb_dino()
elif TASK == "snake_compare":
	snake_compare()
elif TASK == "lab_water":
	lab.lab_water()
elif TASK == "lab_ops":
	lab.lab_ops()
elif TASK == "lab_snake_cost":
	lab.lab_snake_cost()
elif TASK == "lab_speed":
	lab.lab_speed()
elif TASK == "lab_trees":
	lab.lab_trees()
elif TASK == "lab_snake_plants":
	lab.lab_snake_plants()
elif TASK == "lab_cure":
	for how in ["normal", "fert", "one", "giant1", "cure28"]:
		lab.lab_cure(how)
else:
	quick_print("task: unknown TASK", TASK)
quick_print("===== TASK DONE =====")
