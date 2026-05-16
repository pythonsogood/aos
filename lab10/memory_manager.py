from abc import ABC, abstractmethod


class MemoryManager(ABC):
	@abstractmethod
	def allocate(self, process_id: int, allocation_size: int) -> None: ...

	@abstractmethod
	def deallocate(self, process_id: int) -> int: ...

	@property
	@abstractmethod
	def fragmentation_percent(self) -> float: ...

	@property
	@abstractmethod
	def memory_map(self) -> list[tuple[int, int, str]]: ...

	@property
	@abstractmethod
	def visualization(self) -> str: ...


class MemoryManagerFirstFit(MemoryManager):
	def __init__(self, total_memory: int, block_size: int) -> None:
		if total_memory <= 0 or block_size <= 0:
			raise ValueError("Memory sizes must be positive")

		if total_memory % block_size != 0:
			raise ValueError("total_memory must be divisible by block_size")

		self.__block_size = block_size
		self.__blocks: list[int | None] = [None] * (total_memory // block_size)

	def allocate(self, process_id: int, allocation_size: int) -> None:
		if allocation_size <= 0:
			raise ValueError("allocation_size must be positive")

		allocation_blocks = (allocation_size + self.__block_size - 1) // self.__block_size

		current_block_start, current_block_length = None, 0

		for i, block in enumerate(self.__blocks):
			if block is not None:
				current_block_start, current_block_length = None, 0
				continue

			if current_block_start is None:
				current_block_start = i

			current_block_length += 1

			if current_block_length >= allocation_blocks:
				break
		else:
			raise RuntimeError("No free space available")

		for i in range(current_block_start, current_block_start + allocation_blocks):
			self.__blocks[i] = process_id

	def deallocate(self, process_id: int) -> int:
		released = 0

		for i, block in enumerate(self.__blocks):
			if block == process_id:
				self.__blocks[i] = None
				released += 1

		return released * self.__block_size

	@property
	def fragmentation_percent(self) -> float:
		total_free = 0
		largest_contiguous = 0

		start = None

		for i, block in enumerate(self.__blocks):
			if block is None and start is None:
				start = i
			elif block is not None and start is not None:
				length = i - start

				total_free += length
				largest_contiguous = max(largest_contiguous, length)

				start = None

		if start is not None:
			length = len(self.__blocks) - start

			total_free += length
			largest_contiguous = max(largest_contiguous, length)

		if total_free <= 0:
			return 0.0

		external_fragmentation = (total_free - largest_contiguous) / total_free * 100.0

		return round(external_fragmentation, 2)

	@property
	def memory_map(self) -> list[tuple[int, int, str]]:
		result: list[tuple[int, int, str]] = []
		current_owner = self.__blocks[0]
		start_idx = 0

		for i in range(1, len(self.__blocks) + 1):
			if i == len(self.__blocks) or self.__blocks[i] != current_owner:
				owner = f"P{current_owner}" if current_owner is not None else "FREE"
				result.append((start_idx, i - 1, owner))

				if i < len(self.__blocks):
					start_idx = i
					current_owner = self.__blocks[i]

		return result

	@property
	def visualization(self) -> str:
		return "| " + " | ".join(f"P{block}" if block is not None else "FREE" for block in self.__blocks) + " |"


def main() -> None:
	memory: MemoryManager = MemoryManagerFirstFit(512, 32)

	requests: tuple[tuple[int, int], ...] = ((1, 120), (2, 80), (3, 100), (4, 64))

	for pid, req in requests:
		try:
			memory.allocate(pid, req)
		except RuntimeError:
			print(f"Allocation failed for Process P{pid} ({req}MB)")
		else:
			print(f"Allocated {req}MB to Process P{pid}")

	print(f"Memory: {memory.visualization}")
	print(f"Memory Fragmentation: {memory.fragmentation_percent}%")

	release_pid = 3
	released = memory.deallocate(release_pid)
	print(f"Released {released}MB from Process P{release_pid}")

	print(f"Memory: {memory.visualization}")
	print(f"Memory Fragmentation: {memory.fragmentation_percent}%")

	print(f"Memory Map: {memory.memory_map}")


if __name__ == "__main__":
	main()
