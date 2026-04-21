from processor import Processor
from shared_mem import SharedMemory


def main():
	memory = SharedMemory()

	cpu1 = Processor(memory)
	cpu2 = Processor(memory)

	cpu1.read_address(0x0001)
	cpu2.read_address(0x0001)
	cpu2.write_address(0x0002, 30)
	cpu1.write_address(0x0001, 20)
	cpu1.read_address(0x0002)
	cpu2.read_address(0x0002)


if __name__ == "__main__":
	main()
