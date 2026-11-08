# ===== task: what runs inside the sandbox or a leaderboard run =====
# Never press play here: run's go() starts it.
#  - Leaderboard runs: the board is recognised from the starting items
#    (fixed per board), so the same file works for practice and real runs.
#  - Anything else: go() hands the job's name in as JOB (simulate's
#    sim_globals), so nothing needs editing.
# New experiments: a function in lab (or here) + one line in pick(). Never a new window.

import jobs
import dino
import lab
import config

def lb_pumpkins():
	goal = 200000000
	t0 = get_time()
	while num_items(Items.Pumpkin) < goal:
		jobs.pumpkin_round(3600, config.PUMPKIN_PATIENCE, config.PUMPKIN_GAP, goal)
	quick_print("LEADERBOARD pumpkins:", num_items(Items.Pumpkin), "in", get_time() - t0, "s")

def lb_dino():
	goal = 33488928
	t0 = get_time()
	while num_items(Items.Bone) < goal:
		dino.do_dino(-1)
	quick_print("LEADERBOARD bones:", num_items(Items.Bone), "in", get_time() - t0, "s")

def snake_compare():
	# one full snake per cut-off (different random apples each time, so
	# only trust big differences)
	for cut in [0.15, 0.2, 0.3]:
		b0 = num_items(Items.Bone)
		t0 = get_time()
		dino.do_dino(cut)
		quick_print("SNAKE cut", cut, ":", get_time() - t0, "game seconds, bones", num_items(Items.Bone) - b0)

def pick(job):
	if job == "lb_pumpkins":
		lb_pumpkins()
	elif job == "lb_dino":
		lb_dino()
	elif job == "snake_compare":
		snake_compare()
	elif job == "lab_water":
		lab.lab_water()
	elif job == "lab_ops":
		lab.lab_ops()
	elif job == "lab_snake_cost":
		lab.lab_snake_cost()
	elif job == "lab_speed":
		lab.lab_speed()
	elif job == "lab_trees":
		lab.lab_trees()
	elif job == "lab_snake_plants":
		lab.lab_snake_plants()
	elif job == "lab_cure":
		for how in ["normal", "fert", "one", "giant1", "cure28"]:
			lab.lab_cure(how)
	else:
		quick_print("task: unknown job", job)

# Which job? Leaderboards start with only what they need: carrots alone =
# pumpkins, cactus alone = dinosaur. Everything else gets JOB from go().
carrots = num_items(Items.Carrot) > 0
cactus = num_items(Items.Cactus) > 0
if carrots and not cactus:
	job = "lb_pumpkins"
elif cactus and not carrots:
	job = "lb_dino"
else:
	job = JOB
quick_print("===== TASK", job, "=====")
pick(job)
quick_print("===== TASK DONE =====")
