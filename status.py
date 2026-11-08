# ===== status: tells you what the farm is doing =====
# - a readable line in the output window whenever the job changes
# - a different hat per job on the main drone (if HAT_STATUS is on)

from config import MODE_NAME, HAT_STATUS

hats = []          # unlocked hats, filled in the first time
shown = [-1]       # job we last announced

def show(goal, payback, item, run):
	if run == shown[0]:
		return
	shown[0] = run
	quick_print("GOAL", goal, "(payback", payback, ") | FARMING", item, "| JOB", MODE_NAME[run])
	if HAT_STATUS:
		wear(run)

def wear(run):
	if len(hats) == 0:
		for h in Hats:
			# never the dinosaur hat: wearing it starts snake mode!
			if num_unlocked(h) > 0 and h != Hats.Dinosaur_Hat:
				hats.append(h)
	if len(hats) > 1:
		change_hat(hats[run % len(hats)])
