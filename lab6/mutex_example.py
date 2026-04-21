import random
import time
from threading import Lock, Thread


class SharedResource[T]():
	def __init__(self) -> None:
		self.__value = None
		self.__lock = Lock()

	@property
	def value(self) -> T | None:
		with self.__lock:
			return self.__value

	@value.setter
	def value(self, value: T | None) -> None:
		with self.__lock:
			self.__value = value


def job(id: str, resource: SharedResource) -> None:
	for _ in range(3):
		time.sleep(random.uniform(0.05, 0.1))

		print(f"[{time.time_ns()}] Thread {id} is incrementing {resource.value}")

		resource.value = (resource.value or 0) + 1


def main() -> None:
	resource = SharedResource[int]()

	threads = [Thread(target=job, args=(f"Thread-{i}", resource)) for i in range(1, 6)]

	print("Starting threads...")

	for thread in threads:
		thread.start()

	for thread in threads:
		thread.join()

	print(f"All threads finished.\nFinal value of shared resource: {resource.value}")


if __name__ == "__main__":
	main()
