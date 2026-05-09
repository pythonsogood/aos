"""
	Prerequisites:
		GIL disabled Python (free threaded)
"""

import threading


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

	@property
	def initial_value(self) -> int:
		return self.__initial_value

	def reset(self) -> None:
		self.__value = self.__initial_value


def increment(counter: SharedCounter, increments: int = 1, mutex: threading.Lock | None = None, incrementor: int = 1) -> None:
	for _ in range(increments):
		if mutex is not None:
			mutex.acquire()

		counter.value += incrementor

		if mutex is not None:
			mutex.release()

def run_experiment(thread_count: int, increments_per_thread: int) -> None:
	expected_value = thread_count * increments_per_thread

	print(f"Expected value of shared counter: {expected_value}")

	counter = SharedCounter()

	threads = tuple(threading.Thread(target=increment, args=(counter, increments_per_thread)) for _ in range(thread_count))

	for thread in threads:
		thread.start()

	for thread in threads:
		thread.join()

	print(f"Final value of shared counter without mutex: {counter.value}")

	counter.reset()

	mutex = threading.Lock()

	threads = [threading.Thread(target=increment, args=(counter, increments_per_thread, mutex)) for _ in range(thread_count)]

	for thread in threads:
		thread.start()

	for thread in threads:
		thread.join()

	print(f"Final value of shared counter with mutex: {counter.value}")


def main() -> None:
	run_experiment(8, 1000)
	run_experiment(16, 1000)


if __name__ == "__main__":
	main()
