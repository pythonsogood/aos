import logging
import os
import shutil
import subprocess
import time
from collections import deque
from enum import Enum
from typing import Deque, Iterable, NamedTuple

from tabulate import tabulate

logger = logging.getLogger(__name__)
EXECUTABLE = (
	(
		shutil.which("timeout.exe") or os.path.join("C:", "Windows", "System32", "timeout.exe"),
		("/T", "-1", "/NOBREAK"),
	)
	if os.name == "nt"
	else (shutil.which("sleep") or os.path.join("/", "bin", "sleep"), ("infinity",))
)


class ProcessState(Enum):
	NEW = "NEW"
	READY = "READY"
	RUNNING = "RUNNING"
	TERMINATED = "TERMINATED"


class Process:
	def __init__(
		self,
		process_id: int,
		executable: tuple[str, tuple[str, ...]],
		arrival_time: int,
		burst_time: int,
		priority: int = 0,
	) -> None:
		self.__process_id = process_id
		self.__executable = executable[0]
		self.__args = executable[1]
		self.__arrival_time = arrival_time
		self.__burst_time = burst_time
		self.__priority = priority
		self.__state = ProcessState.NEW

		self.__popen: subprocess.Popen | None = None
		self.__remaining_time = self.__burst_time
		self.__completion_time: int | None = None

	@property
	def process_id(self) -> int:
		return self.__process_id

	@property
	def arrival_time(self) -> int:
		return self.__arrival_time

	@property
	def burst_time(self) -> int:
		return self.__burst_time

	@property
	def priority(self) -> int:
		return self.__priority

	@property
	def state(self) -> ProcessState:
		return self.__state

	@state.setter
	def state(self, value: ProcessState) -> None:
		self.__state = value

	@property
	def remaining_time(self) -> int:
		return self.__remaining_time

	@remaining_time.setter
	def remaining_time(self, value: int) -> None:
		self.__remaining_time = value

	@property
	def completion_time(self) -> int | None:
		return self.__completion_time

	@completion_time.setter
	def completion_time(self, value: int | None) -> None:
		self.__completion_time = value

	@property
	def popen_running(self) -> bool:
		return self.__popen is not None and self.__popen.poll() is None

	def execute(self) -> None:
		if self.__popen is not None and self.__popen.poll() is None:
			raise RuntimeError("Process already executed")

		self.__popen = subprocess.Popen((self.__executable, *self.__args), stdout=subprocess.DEVNULL)

	def terminate(self, timeout: float | None = 2.0) -> None:
		if self.__popen is None or self.__popen.poll() is not None:
			return

		self.__popen.terminate()

		try:
			self.__popen.wait(timeout)
		except subprocess.TimeoutExpired:
			self.__popen.kill()
			self.__popen.wait(timeout)

	def clone(self) -> Process:
		return Process(
			self.__process_id,
			(self.__executable, self.__args),
			self.__arrival_time,
			self.__burst_time,
			self.__priority,
		)

	def __str__(self) -> str:
		return f"P{self.__process_id}"


class SchedulerStats(NamedTuple):
	name: str
	average_waiting_time: float
	average_turnaround_time: float
	cpu_utilization_percent: float
	throughput_processes_per_sec: float
	total_time: float


def calculate_stats(name: str, processes: Iterable[Process], busy_time: float, total_time: float) -> SchedulerStats:
	waiting_times: list[int] = []
	turnaround_times: list[int] = []

	for p in processes:
		if p.completion_time is None:
			continue

		turnaround = p.completion_time - p.arrival_time
		waiting = turnaround - p.burst_time

		turnaround_times.append(turnaround)
		waiting_times.append(waiting)

	count = len(turnaround_times) if turnaround_times else 1
	avg_wait = sum(waiting_times) / count
	avg_turnaround = sum(turnaround_times) / count
	cpu_util = (busy_time / total_time * 100.0) if total_time else 0.0
	throughput = (len(turnaround_times) / total_time) if total_time else 0.0

	return SchedulerStats(
		name=name,
		average_waiting_time=round(avg_wait, 2),
		average_turnaround_time=round(avg_turnaround, 2),
		cpu_utilization_percent=round(cpu_util, 2),
		throughput_processes_per_sec=round(throughput, 4),
		total_time=round(total_time, 6),
	)


def run_fcfs(processes: Iterable[Process]) -> SchedulerStats:
	processes = sorted(processes, key=lambda p: (p.arrival_time, p.process_id))
	ready: Deque[Process] = deque()

	idx = 0
	current: Process | None = None

	current_time = 0
	busy_time = 0.0

	started_at = time.monotonic()

	while idx < len(processes) or ready or current is not None:
		while idx < len(processes) and processes[idx].arrival_time <= current_time:
			p = processes[idx]

			p.state = ProcessState.READY
			ready.append(p)

			logger.info(f"Time {current_time}: Process {p} entered READY queue")

			idx += 1

		if current is None and ready:
			current = ready.popleft()

			current.state = ProcessState.RUNNING
			current.execute()

			logger.info(f"Time {current_time}: Process {current} RUNNING")

		if current is not None:
			tick_start = time.monotonic()
			time.sleep(1.0)
			busy_time += time.monotonic() - tick_start

			current.remaining_time -= 1
			if not current.popen_running:
				current.remaining_time = 0

			if current.remaining_time <= 0:
				current.state = ProcessState.TERMINATED
				current.terminate()
				current.completion_time = current_time + 1

				logger.info(f"Time {current_time + 1}: Process {current} TERMINATED")

				current = None

		current_time += 1

	total_time = time.monotonic() - started_at
	stats = calculate_stats("FCFS", processes, busy_time, total_time)

	return stats


def run_round_robin(processes: Iterable[Process], quantum: int = 2) -> SchedulerStats:
	if quantum <= 0:
		raise ValueError("Quantum must be > 0")

	processes = sorted(processes, key=lambda p: (p.arrival_time, p.process_id))
	ready: Deque[Process] = deque()

	idx = 0
	current: Process | None = None

	current_time = 0
	busy_time = 0.0
	quantum_left = 0

	started_at = time.monotonic()

	while idx < len(processes) or ready or current is not None:
		while idx < len(processes) and processes[idx].arrival_time <= current_time:
			p = processes[idx]

			p.state = ProcessState.READY
			ready.append(p)

			logger.info(f"Time {current_time}: Process {p} entered READY queue")

			idx += 1

		if current is None and ready:
			current = ready.popleft()
			quantum_left = quantum

			current.state = ProcessState.RUNNING
			current.execute()

			logger.info(f"Time {current_time}: Process {current} RUNNING")

		if current is not None:
			tick_start = time.monotonic()
			time.sleep(1.0)
			busy_time += time.monotonic() - tick_start

			current.remaining_time -= 1
			if not current.popen_running:
				current.remaining_time = 0

			quantum_left -= 1

			if current.remaining_time <= 0:
				current.state = ProcessState.TERMINATED
				current.terminate()

				current.completion_time = current_time + 1

				logger.info(f"Time {current_time + 1}: Process {current} TERMINATED")

				current = None
			elif quantum_left == 0:
				current.terminate()
				current.state = ProcessState.READY
				ready.append(current)

				logger.info(f"Time {current_time + 1}: Time slice expired for {current} terminated (re-queued)")

				current = None

		current_time += 1

	total_time = time.monotonic() - started_at
	stats = calculate_stats("RR", processes, busy_time, total_time)

	return stats


def main() -> None:
	logging.basicConfig(format="%(message)s", level=logging.INFO)

	workload: tuple[Process, ...] = (
		Process(1, EXECUTABLE, 0, 4, 2),
		Process(2, EXECUTABLE, 1, 2, 1),
		Process(3, EXECUTABLE, 2, 3, 3),
		Process(4, EXECUTABLE, 4, 2, 2),
	)

	quantum = 2

	logger.info("FCFS:")
	stats_fcfs = run_fcfs(p.clone() for p in workload)

	logger.info(f"RR (q={quantum}):")
	stats_rr = run_round_robin((p.clone() for p in workload), quantum)

	logger.info(
		tabulate(
			(
				(
					stat.name,
					stat.average_waiting_time,
					stat.average_turnaround_time,
					stat.cpu_utilization_percent,
					stat.throughput_processes_per_sec,
					stat.total_time,
				)
				for stat in (stats_fcfs, stats_rr)
			),
			headers=("Algorithm", "Avg Waiting Time", "Avg Turnaround", "CPU Utilization", "Throughput", "Total Time"),
			tablefmt="presto",
		)
	)


if __name__ == "__main__":
	main()
