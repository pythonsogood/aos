import logging


def configure_logging(logger: logging.Logger, stdout: bool = False) -> None:
	logger.setLevel(logging.INFO)

	formatter = logging.Formatter("[%(asctime)s | %(levelname)s] %(message)s", datefmt="%Y-%m-%d %H:%M:%S")

	if stdout:
		stdout_handler = logging.StreamHandler()
		stdout_handler.setFormatter(formatter)
		logger.addHandler(stdout_handler)

	file_handler = logging.FileHandler("security_log.txt")
	file_handler.setFormatter(formatter)
	logger.addHandler(file_handler)


def main() -> None:
	logger = logging.getLogger(__name__)
	configure_logging(logger)


if __name__ == "__main__":
	main()
