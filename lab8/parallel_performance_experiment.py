import math
import multiprocessing
import time


def is_prime(num: int) -> bool:
	if num <= 1:
		return False

	for i in range(2, math.floor(math.sqrt(num)) + 1):
		if num % i == 0:
			return False

	return True

def get_primes(lower: int, upper: int) -> list[int]:
	primes: list[int] = []

	for i in range(lower, upper + 1):
		if is_prime(i):
			primes.append(i)

	return primes


def main() -> None:
	pass


if __name__ == "__main__":
	main()
