from __future__ import annotations

from threading import Lock
from typing import TYPE_CHECKING

if TYPE_CHECKING:
	from processor import Processor


class SharedMemory():
	def __init__(self) -> None:
		self.__memory: dict[int, int] = {}
		self.__lock = Lock()
		self.__processors: list[Processor] = []

	def register_processor(self, processor: Processor) -> None:
		self.__processors.append(processor)

	def read(self, address: int) -> int:
		with self.__lock:
			return self.__memory.get(address, 0)

	def write(self, writer: Processor, address: int, value: int) -> None:
		with self.__lock:
			self.__memory[address] = value

			for proc in self.__processors:
				if proc == writer:
					continue

				proc.invalidate_cache(address)
