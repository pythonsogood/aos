import csv
import threading
import time
from typing import Literal, NamedTuple


type ExperimentMode = Literal["Without lock", "With mutex"]


class ExperimentResult(NamedTuple):
	mode: ExperimentMode
	threads: int
	operations_per_thread: int
	run: int
	expected_value: int
	actual_value: int
	lost_updates: int
	runtime_seconds: float


class SharedCounter():
	def __init__(self, initial_value: int = 0) -> None:
		self.__initial_value = initial_value
		self.__value = initial_value

	@property
	def value(self) -> int:
		return self.__value

	@value.setter
	def value(self, value: int) -> None:
		self.__value = value

	def reset(self) -> None:
		self.__value = self.__initial_value


def increment(counter: SharedCounter, increments: int = 1, mutex: threading.Lock | None = None, incrementor: int = 1) -> None:
	for _ in range(increments):
		if mutex is not None:
			mutex.acquire()

		counter.value += incrementor

		if mutex is not None:
			mutex.release()


def run_experiment(mode: str, thread_count: int, operations_per_thread: int, run_number: int) -> ExperimentResult:
	expected_value = thread_count * operations_per_thread
	counter = SharedCounter()
	mutex = threading.Lock()
	threads: list[threading.Thread] = []

	for _ in range(thread_count):
		if mode == "Without lock":
			threads.append(threading.Thread(target=increment, args=(counter, operations_per_thread)))
		else:
			threads.append(threading.Thread(target=increment, args=(counter, operations_per_thread, mutex)))

	start_time = time.perf_counter()
	for thread in threads:
		thread.start()

	for thread in threads:
		thread.join()

	runtime = time.perf_counter() - start_time
	actual_value = counter.value
	lost_updates = expected_value - actual_value

	return ExperimentResult(
		mode=mode,
		threads=thread_count,
		operations_per_thread=operations_per_thread,
		run=run_number,
		expected_value=expected_value,
		actual_value=actual_value,
		lost_updates=lost_updates,
		runtime_seconds=round(runtime, 6),
	)


def main() -> None:
	THREAD_CONFIGS = (8, 16)
	OPERATIONS_PER_THREAD = 10_000
	RUNS_PER_CONFIGURATION = 5

	results: list[ExperimentResult] = []

	for thread_count in THREAD_CONFIGS:
		for mode in ("Without lock", "With mutex"):
			for run_number in range(1, RUNS_PER_CONFIGURATION + 1):
				results.append(run_experiment(mode, thread_count, OPERATIONS_PER_THREAD, run_number))

	with open("synchronization_results.csv", "w", newline="", encoding="utf-8") as csv_file:
		writer = csv.DictWriter(csv_file, fieldnames=list(results[0]._fields))
		writer.writeheader()
		writer.writerows(result._asdict() for result in results)

	for result in results:
		print(
			f"mode={result.mode:12} run={result.run} threads={result.threads:2} "
			f"ops/thread={result.operations_per_thread:5} expected={result.expected_value:6} "
			f"actual={result.actual_value:6} lost_updates={result.lost_updates:6} "
		)


if __name__ == "__main__":
	main()
