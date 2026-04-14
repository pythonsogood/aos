from vm import HyperVisor, VirtualMachine

def simulate_apps(*vm_apps: tuple[VirtualMachine, str, int, int, int]) -> None:
	for vm_app in vm_apps:
		vm_app[0].show_specs()

	for vm, app_name, cpu, memory, storage in vm_apps:
		vm.run_app(app_name, cpu, memory, storage)

	for vm, app_name, cpu, memory, storage in vm_apps:
		stopped_app, utilization = vm.stop_app(app_name, cpu, memory, storage)

		print(f"Resource utilization for {vm.name} - {utilization}")

	for vm_app in vm_apps:
		vm_app[0].show_specs()

def task3() -> None:
	hv = HyperVisor(1, "Hypervisor1")

	vm1 = VirtualMachine(1, "VM1", 2, 8, 500)
	vm2 = VirtualMachine(2, "VM2", 4, 16, 1000)

	apps = (
		("App1", 1, 2, 125),
		("App2", 1, 12, 750),
	)

	hv.create_vm(vm1)
	hv.create_vm(vm2)

	hv.list_vms()

	simulate_apps(
		(vm1, *apps[0]),
		(vm2, *apps[1]),
	)

def task4() -> None:
	hv = HyperVisor(1, "Hypervisor1")

	vm1 = VirtualMachine(1, "VM1", 8, 16, 1000)
	vm2 = VirtualMachine(2, "VM2", 16, 32, 1000)

	apps = (
		("App1", 1, 2, 125),
		("App2", 1, 6, 250),
	)

	hv.create_vm(vm1)
	hv.create_vm(vm2)

	hv.list_vms()

	simulate_apps(
		(vm1, *apps[0]),
		(vm1, *apps[1]),
		(vm2, *apps[0]),
		(vm2, *apps[1]),
	)


def main() -> None:
	# task3()
	task4()

if __name__ == "__main__":
	main()
