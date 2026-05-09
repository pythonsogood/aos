import csv
import functools
import inspect
import math
import multiprocessing
import time
from typing import Literal, TypedDict


def is_prime(number: int) -> bool:
	if number < 2:
		return False

	if number == 2:
		return True

	if number % 2 == 0:
		return False

	for candidate in range(3, int(math.isqrt(number)) + 1, 2):
		if number % candidate == 0:
			return False

	return True

def count_primes(lower: int, upper: int) -> list[int]:
	primes: list[int] = []

	for i in range(lower, upper + 1):
		if is_prime(i):
			primes.append(i)

	return primes

def run_sequential(lower: int, upper: int) -> tuple[list[int], float]:
	start_time = time.perf_counter()

	primes = count_primes(lower, upper)

	elapsed = time.perf_counter() - start_time

	return primes, elapsed

def run_parallel(lower: int, upper: int, workers: int) -> tuple[list[int], float]:
	chunks: list[tuple[int, int]] = []
	chunk_size = (upper - lower) // workers

	for i in range(lower, upper + 1, chunk_size):
		chunks.append((i, min(i + chunk_size - 1, upper)))

	primes: list[int] = []

	with multiprocessing.Pool(processes=workers) as pool:
		start_time = time.perf_counter()

		primes += functools.reduce(lambda a, b: a + b, pool.starmap(count_primes, chunks))

		elapsed = time.perf_counter() - start_time

	return primes, elapsed


def main() -> None:
	class Result(TypedDict):
		mode: Literal["sequential", "parallel"]
		workers: int
		problem_size: int
		runtime_seconds: float
		speedup: float
		efficiency: float


	LOWER = 2
	UPPER = 1_000_000
	WORKERS = 8

	primes, sequential_time = run_sequential(LOWER, UPPER)

	results: list[Result] = [
		Result(
			mode="sequential",
			workers=1,
			problem_size=len(primes),
			runtime_seconds=round(sequential_time, 6),
			speedup=1.0,
			efficiency=1.0,
		)
	]

	for workers in range(2, min(WORKERS, multiprocessing.cpu_count()) + 1, 2):
		parallel_primes, parallel_time = run_parallel(LOWER, UPPER, workers)

		speedup = sequential_time / parallel_time
		efficiency = speedup / workers

		results.append(
			Result(
				mode="parallel",
				workers=workers,
				problem_size=len(parallel_primes),
				runtime_seconds=round(parallel_time, 6),
				speedup=round(speedup, 6),
				efficiency=round(efficiency, 6),
			)
		)

	with open("parallel_results.csv", "w", newline="", encoding="utf-8") as csv_file:
		writer = csv.DictWriter(csv_file, fieldnames=inspect.get_annotations(Result).keys())
		writer.writeheader()
		writer.writerows(results)

	for row in results:
		print(row)


if __name__ == "__main__":
	main()
