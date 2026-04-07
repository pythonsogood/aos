import os

def calculate_average_score(file_name: os.PathLike[str] = "students.txt") -> float:
	score_count, score_total = 0.0, 0.0

	with open(file_name, encoding="utf-8") as f:
		for line in f.readlines():
			name, _score = line.split(" ")
			score = float(_score)

			score_total += score
			score_count += 1

	return score_total / score_count if score_count > 0 else 0.0


if __name__ == "__main__":
	print(f"Average score: {calculate_average_score()}")
