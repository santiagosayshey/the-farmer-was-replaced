# ===== stats: measure what each job actually does =====
# Every job is timed and its item gains are counted. Jobs can also report
# their own numbers ("extra"), like how many pumpkin blocks merged.
# report() prints a summary to the output window (also saved to output.txt).

from config import MODE_NAME, TRACKED

book = dict()     # mode -> {"rounds", "secs", "gain": {item: n}, "extra": {name: n}}

def start():
	have = dict()
	for item in TRACKED:
		have[item] = num_items(item)
	return [get_time(), have]

def finish(mode, token, extra):
	if not (mode in book):
		book[mode] = {"rounds": 0, "secs": 0, "gain": dict(), "extra": dict()}
	b = book[mode]
	b["rounds"] += 1
	b["secs"] += get_time() - token[0]
	gain = b["gain"]
	for item in TRACKED:
		d = num_items(item) - token[1][item]
		if d != 0:
			if item in gain:
				gain[item] += d
			else:
				gain[item] = d
	ex = b["extra"]
	for name in extra:
		if name in ex:
			ex[name] += extra[name]
		else:
			ex[name] = extra[name]

def report():
	quick_print("===== STATS =====")
	for mode in book:
		b = book[mode]
		mins = b["secs"] / 60
		if mins <= 0:
			mins = 0.0001
		line = "STATS " + MODE_NAME[mode] + ": " + str(b["rounds"]) + " rounds, " + str(b["secs"] // 1) + "s |"
		gain = b["gain"]
		for item in gain:
			if gain[item] > 0:
				line = line + " " + str(item) + " +" + str(gain[item] / mins // 1) + "/min"
		ex = b["extra"]
		if len(ex) > 0:
			line = line + " |"
			for name in ex:
				line = line + " " + name + ": " + str(ex[name])
		quick_print(line)
