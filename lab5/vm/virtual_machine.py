from abc import ABC
from collections.abc import Hashable
from typing import NamedTuple


class RunningApplication(NamedTuple):
	name: str
	cpu: int
	memory: int
	storage: int


class VirtualMachineResource[T: int | float](NamedTuple):
	allocated: T
	free: T
	total: T

	@classmethod
	def from_allocated(cls, allocated: T, total: T) -> VirtualMachineResource[T]:
		return cls(allocated=allocated, free=total - allocated, total=total)

	@classmethod
	def from_free(cls, free: T, total: T) -> VirtualMachineResource[T]:
		return cls(allocated=total - free, free=free, total=total)


class VirtualMachineResources(NamedTuple):
	cpu: VirtualMachineResource[int]
	memory: VirtualMachineResource[int]
	storage: VirtualMachineResource[int]


class VirtualMachineABC[I: Hashable](ABC):
	def __init__(self, id: I, name: str, cpu: int, memory: int, storage: int) -> None:
		self.__id = id
		self.__name = name
		self.__cpu = cpu
		self.__memory = memory
		self.__storage = storage
		self.__running_applications: list[RunningApplication] = []

	@property
	def id(self) -> I:
		return self.__id

	@property
	def name(self) -> str:
		return self.__name

	@property
	def cpu(self) -> int:
		return self.__cpu

	@property
	def memory(self) -> int:
		return self.__memory

	@property
	def storage(self) -> int:
		return self.__storage

	@property
	def cpu_allocated(self) -> int:
		cpu = 0

		for app in self.running_applications:
			cpu += app.cpu

		return min(cpu, self.cpu)

	@property
	def cpu_free(self) -> int:
		return self.cpu - self.cpu_allocated

	@property
	def memory_allocated(self) -> int:
		memory = 0

		for app in self.running_applications:
			memory += app.memory

		return min(memory, self.memory)

	@property
	def memory_free(self) -> int:
		return self.memory - self.memory_allocated

	@property
	def storage_allocated(self) -> int:
		storage = 0

		for app in self.running_applications:
			storage += app.storage

		return min(storage, self.storage)

	@property
	def storage_free(self) -> int:
		return self.storage - self.storage_allocated

	@property
	def running_applications(self) -> tuple[RunningApplication, ...]:
		return tuple(self.__running_applications)

	def run_app(self, app: str, cpu: int, memory: int, storage: int) -> RunningApplication:
		if self.cpu_free < cpu:
			raise ValueError("Not enough CPU")

		if self.memory_free < memory:
			raise ValueError("Not enough Memory")

		if self.storage_free < storage:
			raise ValueError("Not enough Storage")

		running_app = RunningApplication(app, cpu, memory, storage)
		self.__running_applications.append(running_app)

		return running_app

	def stop_app(self, app: str, cpu: int, memory: int, storage: int) -> RunningApplication:
		for i, running_app in enumerate(self.__running_applications):
			if running_app.name == app and running_app.cpu == cpu and running_app.memory == memory and running_app.storage == storage:
				return self.__running_applications.pop(i)

		raise KeyError

	def show_specs(self) -> None:
		print(str(self))

	def resources(self) -> VirtualMachineResources:
		return VirtualMachineResources(
			cpu=VirtualMachineResource.from_allocated(self.cpu_allocated, self.cpu),
			memory=VirtualMachineResource.from_allocated(self.memory_allocated, self.memory),
			storage=VirtualMachineResource.from_allocated(self.storage_allocated, self.storage),
		)

	def __str__(self) -> str:
		return f"VM Name: {self.name}, CPU: {self.cpu_free}/{self.cpu}, Memory: {self.memory_free}/{self.memory}, Storage: {self.storage_free}/{self.storage}"

	def __repr__(self) -> str:
		return f"{self.__class__.__name__}(id={self.id}, name={self.name}, cpu={self.cpu}, memory={self.memory}, storage={self.storage})"

	def __hash__(self) -> int:
		return hash(f"VirtualMachine {self.id}")


class VirtualMachineResourceUtilization(NamedTuple):
	cpu: float
	memory: float
	storage: float

	def __str__(self) -> str:
		return f"CPU: {self.cpu:.1f}%, Memory: {self.memory:.1f}%, Storage: {self.storage:.1f}%"


class VirtualMachine(VirtualMachineABC[int]):
	def run_app(self, app: str, cpu: int, memory: int, storage: int) -> RunningApplication:
		running_app = super().run_app(app, cpu, memory, storage)

		print(f"Running {running_app.name} on {self.name}")

		return running_app

	def stop_app(self, app: str, cpu: int, memory: int, storage: int) -> tuple[RunningApplication, VirtualMachineResourceUtilization]:
		resources_before = self.resources()

		running_app = super().stop_app(app, cpu, memory, storage)

		resources = self.resources()

		print(f"Stopped {running_app.name} on {self.name}. Freed up CPU: {running_app.cpu}, Memory: {running_app.memory}, Storage: {running_app.storage}")

		return running_app, VirtualMachineResourceUtilization(
			cpu=(resources_before.cpu.allocated - resources.cpu.allocated) / self.cpu * 100,
			memory=(resources_before.memory.allocated - resources.memory.allocated) / self.memory * 100,
			storage=(resources_before.storage.allocated - resources.storage.allocated) / self.storage * 100,
		)
