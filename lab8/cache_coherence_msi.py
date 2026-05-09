from enum import Enum
from typing import NamedTuple, TypedDict


type ProcessorID = int


class MSIState(Enum):
	MODIFIED = 1
	SHARED = 0
	INVALID = -1


class CacheSnapshot(NamedTuple):
	value: int
	state: MSIState


class ProcessorStats(TypedDict):
	reads: int
	writes: int
	cache_hits: int
	cache_misses: int
	invalidations: int
	write_backs: int


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

	@property
	def memory(self) -> dict[int, int]:
		return self.__memory

	def read(self, address: int) -> int:
		return self.memory.get(address, 0)

	def write(self, address: int, value: int) -> None:
		self.memory[address] = value

	def snapshot(self) -> dict[int, int]:
		return dict(self.memory)


class Processor():
	def __init__(self, processor_id: ProcessorID, bus: "Bus") -> None:
		self.__processor_id = processor_id
		self.__cache: dict[int, CacheLine] = {}
		self.__bus: "Bus" = bus

	@property
	def processor_id(self) -> int:
		return self.__processor_id

	@property
	def cache(self) -> dict[int, CacheLine]:
		return self.__cache

	@property
	def bus(self) -> "Bus":
		return self.__bus

	@property
	def shared_memory(self) -> SharedMemory:
		return self.bus.shared_memory

	@property
	def statistics(self) -> "Statistics":
		return self.bus.statistics

	def read(self, address: int) -> int:
		self.statistics.record_read(self.processor_id)

		line = self.cache.get(address)

		if line is not None and line.state != MSIState.INVALID:
			self.statistics.record_cache_hit(self.processor_id)

			return line.value

		self.statistics.record_cache_miss(self.processor_id)

		value = self.shared_memory.read(address)

		if line is not None:
			line.value = value
			line.state = MSIState.SHARED
		else:
			self.cache[address] = CacheLine(address, value)
			self.cache[address].state = MSIState.SHARED

		return value

	def write(self, address: int, value: int) -> None:
		self.statistics.record_write(self.processor_id)

		line = self.cache.get(address)

		if line is not None and line.state == MSIState.MODIFIED:
			self.statistics.record_cache_hit(self.processor_id)

			line.value = value

			return

		self.statistics.record_cache_miss(self.processor_id)

		if self.__bus is not None:
			self.__bus.invalidate_others(self.processor_id, address)

		if line is not None:
			line.value = value
			line.state = MSIState.MODIFIED
		else:
			self.cache[address] = CacheLine(address=address, value=value)
			self.cache[address].state = MSIState.MODIFIED

	def invalidate(self, address: int) -> None:
		line = self.cache.get(address)

		if line is None or line.state == MSIState.INVALID:
			return

		if line.state == MSIState.MODIFIED:
			self.flush(address)

		self.statistics.record_invalidation(self.processor_id)

		line.state = MSIState.INVALID

	def flush(self, address: int) -> None:
		line = self.cache.get(address)

		if line is None or line.state != MSIState.MODIFIED:
			return

		self.statistics.record_write_back(self.processor_id)

		self.shared_memory.write(address, line.value)

	def cache_snapshot(self) -> dict[int, CacheSnapshot]:
		return {
			line.address: CacheSnapshot(value=line.value, state=line.state)
			for line in sorted(self.__cache.values(), key=lambda x: hex(x.address))
		}


class Bus():
	def __init__(self) -> None:
		self.__shared_memory = SharedMemory()
		self.__statistics = Statistics()
		self.__processors: list[Processor] = []

	@property
	def shared_memory(self) -> SharedMemory:
		return self.__shared_memory

	@property
	def statistics(self) -> "Statistics":
		return self.__statistics

	@property
	def processors(self) -> list[Processor]:
		return self.__processors

	def add_processor(self) -> Processor:
		processor = Processor(
			(self.processors[-1].processor_id + 1) if self.processors else 0,
			self.shared_memory,
			self
		)

		self.processors.append(processor)

		return processor

	def invalidate_others(self, processor_id: ProcessorID, address: int) -> None:
		for processor in self.processors:
			if processor.processor_id == processor_id:
				continue

			processor.invalidate(address)

	def read(self, processor_id: ProcessorID, address: int) -> int:
		if processor_id > len(self.processors):
			raise IndexError(f"Processor with id {processor_id} does not exist")

		return self.processors[processor_id].read(address)

	def write(self, processor_id: ProcessorID, address: int, value: int) -> None:
		if processor_id > len(self.processors):
			raise IndexError(f"Processor with id {processor_id} does not exist")

		return self.processors[processor_id].write(address, value)


class Statistics():
	def __init__(self) -> None:
		self.__stats: dict[ProcessorID, ProcessorStats] = {}

	@property
	def stats(self) -> dict[ProcessorID, ProcessorStats]:
		return self.__stats

	def _record(self, processor_id: ProcessorID, name: str) -> None:
		if processor_id not in self.__stats:
			self.__stats[processor_id] = ProcessorStats(
				reads=0,
				writes=0,
				cache_hits=0,
				cache_misses=0,
				invalidations=0,
				write_backs=0,
			)

		self.__stats[processor_id][name] += 1

	def record_read(self, processor_id: ProcessorID) -> None:
		self._record(processor_id, "reads")

	def record_write(self, processor_id: ProcessorID) -> None:
		self._record(processor_id, "writes")

	def record_cache_hit(self, processor_id: ProcessorID) -> None:
		self._record(processor_id, "cache_hits")

	def record_cache_miss(self, processor_id: ProcessorID) -> None:
		self._record(processor_id, "cache_misses")

	def record_invalidation(self, processor_id: ProcessorID) -> None:
		self._record(processor_id, "invalidations")

	def record_write_back(self, processor_id: ProcessorID) -> None:
		self._record(processor_id, "write_backs")

	def snapshot(self) -> dict[ProcessorID, ProcessorStats]:
		return dict(self.stats)
