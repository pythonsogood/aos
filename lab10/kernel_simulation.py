import datetime
import logging
import math
import os
import time
from enum import Enum

from tabulate import tabulate

from memory_manager import MemoryManager, MemoryManagerFirstFit
from process_scheduler import EXECUTABLE, Process, SchedulerStats, run_fcfs

type StrOrBytesPath = str | bytes | os.PathLike

logger = logging.getLogger(__name__)


class InterruptType(Enum):
	Timer = "Timer"
	IO = "I/O"
	Keyboard = "Keyboard"
	SoftwareException = "Software exception"


class KernelSimulation:
	def __init__(self) -> None:
		self.__memory: MemoryManager = MemoryManagerFirstFit(1024, 64)
		self.__processes: dict[int, Process] = {}

	@property
	def memory(self) -> MemoryManager:
		return self.__memory

	def create_process(
		self, process_id: int, executable: tuple[str, tuple[str, ...]], burst_time: int, priority: int = 0
	) -> bool:
		logger.info(f"[USER MODE] request -> create_process({process_id})")
		logger.info("[KERNEL MODE] System call handler activated")

		if process_id in self.__processes:
			logger.info(f"SYSTEM CALL FAILED: create_process({process_id}) already exists")
			return False

		process = Process(
			process_id,
			executable,
			0,
			burst_time,
			priority,
		)
		self.__processes[process_id] = process

		logger.info(f"SYSTEM CALL: create_process({process_id}) -> OK")

		return True

	def terminate_process(self, process_id: int) -> bool:
		logger.info(f"[USER MODE] request -> terminate_process({process_id})")
		logger.info("[KERNEL MODE] System call handler activated")

		process = self.__processes.get(process_id)
		if process is None:
			logger.info(f"SYSTEM CALL FAILED: terminate_process({process_id}) not found")
			return False

		process.terminate()

		released = self.__memory.deallocate(process_id)

		del self.__processes[process_id]

		logger.info(f"SYSTEM CALL: terminate_process({process_id}), released -> {released}MB")

		return True

	def allocate_memory(self, process_id: int, request_mb: int) -> bool:
		logger.info(f"[USER MODE] request -> allocate_memory({process_id})")
		logger.info("[KERNEL MODE] System call handler activated")

		process = self.__processes.get(process_id)
		if process is None:
			logger.info(f"SYSTEM CALL FAILED: allocate_memory({process_id}) process not found")
			return False

		try:
			self.__memory.allocate(process_id, request_mb)
		except RuntimeError:
			logger.info(f"MEMORY ALLOCATION FAILED: {process} -> {request_mb}MB")

			return False
		else:
			logger.info(f"MEMORY ALLOCATED: {process} -> {request_mb}MB")

		return True

	def read_file(self, path: StrOrBytesPath) -> bytes:
		file_path = os.path.normpath(path)

		logger.info(f"[USER MODE] request -> read_file({file_path})")
		logger.info("[KERNEL MODE] System call handler activated")

		if not os.path.isfile(file_path):
			logger.info(f"SYSTEM CALL FAILED: read_file({file_path}) not found")

			return b""

		with open(file_path, "rb") as f:
			content = f.read()

		logger.info(f"SYSTEM CALL: read_file({file_path}) -> {len(content)} bytes")

		return content

	def get_system_time(self) -> int:
		logger.info("[USER MODE] request -> get_system_time()")
		logger.info("[KERNEL MODE] System call handler activated")

		now = datetime.datetime.now()

		logger.info(f"SYSTEM CALL: get_system_time() -> {now.isoformat(timespec='seconds')}")

		return math.floor(now.timestamp())

	def interrupt(self, interrupt_type: InterruptType, *args) -> None:
		"""
		User-space Python cannot:
			send real Timer Interrupt
			generate a real I/O and keyboard IRQ directly
			call software exception for external process

		So I left this method simulated (log output only)
		"""

		match interrupt_type:
			case InterruptType.Timer:
				logger.info("INTERRUPT: TIMER")
				logger.info("[SCHEDULER] Context switch performed")

			case InterruptType.IO:
				logger.info(f"INTERRUPT: IO ({args[0]})" if args else "INTERRUPT: IO")
				logger.info("[KERNEL MODE] I/O completion handled")

			case InterruptType.Keyboard:
				logger.info(f"INTERRUPT: KEYBOARD ({args[0]})" if args else "INTERRUPT: KEYBOARD")
				logger.info("[KERNEL MODE] Input event dispatched")

			case InterruptType.SoftwareException:
				logger.info(f"INTERRUPT: SOFTWARE EXCEPTION ({args[0]})" if args else "INTERRUPT: SOFTWARE EXCEPTION")
				logger.info("[KERNEL MODE] Exception handler executed")

	def run_scheduler(self) -> SchedulerStats:
		logger.info("[KERNEL MODE] Running scheduler (FCFS)")

		stats = run_fcfs(self.__processes.values())

		stats_pretty = tabulate(
			(
				(
					stats.average_waiting_time,
					stats.average_turnaround_time,
					stats.cpu_utilization_percent,
					stats.throughput_processes_per_sec,
					stats.total_time,
				),
			),
			headers=(
				"Avg Waiting Time",
				"Avg Turnaround",
				"CPU Utilization",
				"Throughput",
				"Total Time",
			),
			tablefmt="presto",
		)
		logger.info(f"[SCHEDULER] Stats:\n{stats_pretty}")

		return stats


def main() -> None:
	logger.setLevel(logging.INFO)

	formatter = logging.Formatter("[%(asctime)s] %(message)s", datefmt="%H:%M:%S")

	stdout_handler = logging.StreamHandler()
	stdout_handler.setFormatter(formatter)
	logger.addHandler(stdout_handler)

	file_handler = logging.FileHandler("kernel_log.txt")
	file_handler.setFormatter(formatter)
	logger.addHandler(file_handler)

	kernel = KernelSimulation()

	kernel.create_process(1, EXECUTABLE, burst_time=5, priority=1)
	kernel.create_process(2, EXECUTABLE, burst_time=3, priority=2)

	kernel.allocate_memory(1, 128)
	kernel.allocate_memory(2, 192)

	kernel.read_file("kernel_log.txt")
	kernel.get_system_time()

	kernel.interrupt(InterruptType.Timer)
	time.sleep(0.05)
	kernel.interrupt(InterruptType.IO, "network0")
	kernel.interrupt(InterruptType.Keyboard, "K")
	kernel.interrupt(InterruptType.SoftwareException, "division by zero")

	kernel.run_scheduler()
	kernel.terminate_process(1)

	logger.info(f"Current Memory: {kernel.memory.visualization}")
	logger.info(f"Fragmentation: {kernel.memory.fragmentation_percent}%")


if __name__ == "__main__":
	main()
