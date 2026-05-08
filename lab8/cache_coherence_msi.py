from enum import Enum
from typing import NamedTuple


type ProcessorID = int


class MSIState(Enum):
	MODIFIED = 1
	SHARED = 0
	INVALID = -1


class CacheSnapshot(NamedTuple):
	value: int
	state: MSIState


class CacheLine():
	def __init__(self, address: int, value: int = 0) -> None:
		self.__address = address
		self.__value = value
		self.__state = None

	@property
	def address(self) -> int:
		return self.__address

	@property
	def value(self) -> int:
		return self.__value

	@value.setter
	def value(self, new_value: int) -> None:
		self.__value = new_value

	@property
	def state(self) -> MSIState | None:
		return self.__state

	@state.setter
	def state(self, new_state: MSIState | None) -> None:
		self.__state = new_state


class SharedMemory():
	def __init__(self) -> None:
		self.__memory: dict[int, int] = {}

	def read(self, address: int) -> int:
		return self.__memory.get(address, 0)

	def write(self, address: int, value: int) -> None:
		self.__memory[address] = value

	def snapshot(self) -> dict[int, int]:
		return dict(self.__memory)


class Processor():
	def __init__(self, processor_id: ProcessorID, shared_memory: SharedMemory, bus: "Bus") -> None:
		self.__processor_id = processor_id
		self.__shared_memory = shared_memory
		self.__cache: dict[int, CacheLine] = {}
		self.__bus: "Bus" = bus

	@property
	def processor_id(self) -> int:
		return self.__processor_id

	def read(self, address: int) -> int:
		line = self.__cache.get(address)

		if line is not None and line.state != MSIState.INVALID:
			return line.value

		value = self.__shared_memory.read(address)

		if line is not None:
			line.value = value
			line.state = MSIState.SHARED
		else:
			self.__cache[address] = CacheLine(address, value)
			self.__cache[address].state = MSIState.SHARED

		return value

	def write(self, address: int, value: int) -> None:
		line = self.__cache.get(address)

		if line is not None and line.state == MSIState.MODIFIED:
			line.value = value
			return

		if self.__bus is not None:
			self.__bus.invalidate_others(self.processor_id, address)

		if line is not None:
			line.value = value
			line.state = MSIState.MODIFIED
		else:
			self.__cache[address] = CacheLine(address=address, value=value)
			self.__cache[address].state = MSIState.MODIFIED

	def invalidate(self, address: int) -> None:
		line = self.__cache.get(address)

		if line is None or line.state == MSIState.INVALID:
			return

		if line.state == MSIState.MODIFIED:
			self.flush(address)

		line.state = MSIState.INVALID

	def flush(self, address: int) -> None:
		line = self.__cache.get(address)

		if line is None or line.state != MSIState.MODIFIED:
			return

		self.__shared_memory.write(address, line.value)

	def cache_snapshot(self) -> dict[int, CacheSnapshot]:
		return {
			line.address: CacheSnapshot(value=line.value, state=line.state)
			for line in sorted(self.__cache.values(), key=lambda x: hex(x.address))
		}


class Bus():
	def __init__(self) -> None:
		self.__shared_memory = SharedMemory()
		self.__processors: list[Processor] = []

	def add_processor(self) -> Processor:
		processor = Processor(
			(self.__processors[-1].processor_id + 1) if self.__processors else 0,
			self.__shared_memory,
			self
		)

		self.__processors.append(processor)

		return processor

	def invalidate_others(self, processor_id: ProcessorID, address: int) -> None:
		for processor in self.__processors:
			if processor.processor_id == processor_id:
				continue

			processor.invalidate(address)

	def read(self, processor_id: ProcessorID, address: int) -> int:
		if processor_id > len(self.__processors):
			raise IndexError(f"Processor with id {processor_id} does not exist")

		return self.__processors[processor_id].read(address)

	def write(self, processor_id: ProcessorID, address: int, value: int) -> None:
		if processor_id > len(self.__processors):
			raise IndexError(f"Processor with id {processor_id} does not exist")

		return self.__processors[processor_id].write(address, value)


class Statistics():
	def __init__(self) -> None:
		self.__stats: dict[ProcessorID, float] = {}
