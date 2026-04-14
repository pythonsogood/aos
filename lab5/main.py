from vm import HyperVisor, VirtualMachine


def main() -> None:
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

	for vm in hv.vms:
		vm.show_specs()

	vm1.run_app(*apps[0])
	vm2.run_app(*apps[1])

	for vm in (vm1, vm2):
		for app in vm.running_applications:
			stopped_app, utilization = vm.stop_app(*app)

			print(f"Resource utilization for {vm.name} - {utilization}")

	for vm in (vm1, vm2):
		vm.show_specs()


if __name__ == "__main__":
	main()
