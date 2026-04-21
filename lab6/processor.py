from threading import Lock
from typing import TypedDict

from shared_mem import SharedMemory


class ProcessorCache(TypedDict):
	value: int
	valid_state: bool


class Processor():
	__ID_INCREMENTOR = 0
	__ID_INCREMENTOR_LOCK = Lock()

	def __init__(self, shared_memory: SharedMemory) -> None:
		with self.__class__.__ID_INCREMENTOR_LOCK:
			self.__id = self.__class__.__ID_INCREMENTOR
			self.__class__.__ID_INCREMENTOR += 1

		self.__shared_memory = shared_memory
		self.__cache: dict[int, ProcessorCache] = {}

		shared_memory.register_processor(self)

	def invalidate_cache(self, address: int) -> None:
		if address not in self.__cache:
			return

		self.__cache[address]["valid_state"] = False

	def read_address(self, address: int) -> int:
		if address in self.__cache:
			if self.__cache[address]["valid_state"]:
				value = self.__cache[address]["value"]

				print(f"Processor {self.__id} reads from memory (CACHE HIT): Value at address 0x{address:04x} = {value}")

				return value

		value = self.__shared_memory.read(address)

		print(f"Processor {self.__id} reads from memory (CACHE MISS): Value at address 0x{address:04x} = {value}")

		if address not in self.__cache:
			self.__cache[address] = {}

		self.__cache[address]["value"] = value
		self.__cache[address]["valid_state"] = True

		return value

	def write_address(self, address: int, value: int) -> None:
		self.__shared_memory.write(self, address, value)

		print(f"Processor {self.__id} writes to memory: Set value at address 0x{address:04x} = {value}")

		if address not in self.__cache:
			self.__cache[address] = {}

		self.__cache[address]["value"] = value
		self.__cache[address]["valid_state"] = True

	def __hash__(self) -> int:
		return hash(self.__id)

	def __eq__(self, value: object, /) -> bool:
		if not isinstance(value, self.__class__):
			return False

		return hash(self) == hash(value)
