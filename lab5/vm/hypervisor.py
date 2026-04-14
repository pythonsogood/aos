from abc import ABC
from collections.abc import Hashable

from .virtual_machine import VirtualMachineABC


class HyperVisorABC[I: Hashable](ABC):
	def __init__(self, id: I, name: str) -> None:
		self.__id = id
		self.__name = name
		self.__vms: dict[Hashable, VirtualMachineABC] = {}

	@property
	def id(self) -> I:
		return self.__id

	@property
	def name(self) -> str:
		return self.__name

	@property
	def vms(self) -> set[VirtualMachineABC]:
		return set(self.__vms.values())

	def create_vm(self, vm: VirtualMachineABC) -> None:
		if vm.id in self.__vms:
			raise ValueError(f"Virtual Machine with id {vm.id} already exists")

		self.__vms[vm.id] = vm

	def remove_vm(self, vm: VirtualMachineABC) -> None:
		del self.__vms[vm.id]

	def list_vms(self) -> None:
		print("\n".join(f"VM ID: {vm.id}, VM Name: {vm.name}" for vm in self.__vms.values()))

	def __str__(self) -> str:
		return repr(self)

	def __repr__(self) -> str:
		return f"{self.__class__.__name__}(id={self.id}, name={self.name})"

	def __hash__(self) -> int:
		return hash(f"HyperVisor {self.id}")

class HyperVisor(HyperVisorABC[int]):
	def create_vm(self, vm: VirtualMachineABC) -> None:
		result = super().create_vm(vm)

		print(f"Created VM {vm.name} on {self.name}")

		return result

	def remove_vm(self, vm: VirtualMachineABC) -> None:
		result = super().remove_vm(vm)

		print(f"Removed VM {vm.name} on {self.name}")

		return result
