import argparse
import datetime
import hashlib
import hmac
import json
import os
import threading
from dataclasses import asdict, dataclass
from getpass import getpass
from typing import ClassVar

import bcrypt


@dataclass()
class User():
	CHECKSUM_SECRET: ClassVar[str] = r"0KTl~nI7Fasvo2DScbyXkOVAykXE1w%|"
	MAX_ATTEMPTS: ClassVar[int] = 3
	LOCK_DURATION: ClassVar[datetime.timedelta] = datetime.timedelta(seconds=10)

	username: str
	password_hash: str
	attempts: int = 0
	lock: int = 0
	checksum: str = ""

	def is_locked(self) -> bool:
		now = datetime.datetime.now(datetime.timezone.utc)
		lock_until = datetime.datetime.fromtimestamp(self.lock, datetime.timezone.utc)

		return lock_until > now

	def lock_account(self) -> None:
		now = datetime.datetime.now(datetime.timezone.utc)

		self.lock = round((now + User.LOCK_DURATION).timestamp())

	def verify_password(self, password: str) -> bool:
		return User.check_password(password, self.password_hash)

	def generate_checksum(self) -> str:
		return hmac.new(
			self.__class__.CHECKSUM_SECRET.encode("utf-8"),
			f"{self.username}.{self.password_hash}.{self.lock}".encode("utf-8"),
			digestmod=hashlib.sha256
		).hexdigest()

	def update_checksum(self) -> None:
		self.checksum = self.generate_checksum()

	def verify_checksum(self) -> bool:
		return self.checksum == self.generate_checksum()

	@classmethod
	def new(cls, username: str, password: str) -> User:
		user = cls(username=username, password_hash=cls.hash_password(password), lock=0)
		user.update_checksum()
		return user

	@staticmethod
	def hash_password(password: str) -> str:
		return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).hex()

	@staticmethod
	def check_password(password: str, password_hash: str) -> bool:
		return bcrypt.checkpw(password.encode("utf-8"), bytes.fromhex(password_hash))

	@staticmethod
	def dict_factory(x):
		return {k: v for k, v in x if k != "username"}

class Database():
	def __init__(self, filepath: os.PathLike) -> None:
		self.__filepath = os.path.normpath(filepath)
		self.__lock = threading.Lock()

		if not os.path.exists(self.__filepath):
			directory, filename = os.path.split(self.__filepath)

			with self.__lock:
				os.makedirs(os.path.normpath(directory), exist_ok=True)

				with open(self.__filepath, "w", encoding="utf-8") as f:
					f.write("{}")
		else:
			with self.__lock:
				with open(self.__filepath, "r+", encoding="utf-8") as f:
					try:
						db = json.loads(f.read())
					except json.decoder.JSONDecodeError:
						db = None

					if not isinstance(db, dict):
						f.seek(0)
						f.truncate(0)
						f.write("{}")
					else:
						invalid_usernames = []

						for username, payload in db.items():
							try:
								user = User(username=username, **payload)
							except Exception:
								invalid_usernames.append(username)
							else:
								if not user.verify_checksum():
									invalid_usernames.append(username)

						if invalid_usernames:
							for username in invalid_usernames:
								del db[username]

							f.seek(0)
							f.truncate()
							f.write(json.dumps(db, ensure_ascii=False, indent="\t"))

	def register_user(self, user: User) -> None:
		with self.__lock:
			with open(self.__filepath, "r+", encoding="utf-8") as f:
				db = json.loads(f.read())

				if user.username in db:
					db_user = User(user.username, **db[user.username])

					if db_user.verify_checksum():
						raise KeyError("User already exists")

				db[user.username] = asdict(user, dict_factory=User.dict_factory)

				f.seek(0)
				f.truncate(0)
				f.write(json.dumps(db, ensure_ascii=False, indent="\t"))

	def login_user(self, username: str, password: str) -> User:
		user = self.get_user(username)

		if user is None:
			raise ValueError("Username does not exists.")

		if user.is_locked():
			raise ValueError("Account temporarily locked.")

		if not user.verify_password(password):
			if user.attempts + 1 >= User.MAX_ATTEMPTS:
				user.lock_account()

				with self.__lock:
					with open(self.__filepath, "r+", encoding="utf-8") as f:
						db = json.loads(f.read())

						if user.username in db:
							db[user.username]["lock"] = user.lock

							db_user = User(user.username, **db[user.username])
							db_user.update_checksum()

							db[user.username]["checksum"] = db_user.checksum
						else:
							user.update_checksum()
							db[user.username] = asdict(user, dict_factory=User.dict_factory)

						f.seek(0)
						f.truncate(0)
						f.write(json.dumps(db, ensure_ascii=False, indent="\t"))

				raise ValueError("Access denied.\nAccount temporarily locked.")
			else:
				with self.__lock:
					with open(self.__filepath, "r+", encoding="utf-8") as f:
						db = json.loads(f.read())

						if user.username not in db:
							db[user.username] = asdict(user, dict_factory=User.dict_factory)

						db[user.username]["attempts"] = max(db[user.username]["attempts"] + 1, 1)

						db_user = User(user.username, **db[user.username])
						db_user.update_checksum()

						db[user.username]["checksum"] = db_user.checksum

						f.seek(0)
						f.truncate(0)
						f.write(json.dumps(db, ensure_ascii=False, indent="\t"))

			raise ValueError("Access denied.")

		if user.attempts > 0:
			user.attempts = 0

			with self.__lock:
				with open(self.__filepath, "r+", encoding="utf-8") as f:
					db = json.loads(f.read())

					if user.username not in db:
						db[user.username] = asdict(user, dict_factory=User.dict_factory)

					db[user.username]["attempts"] = user.attempts

					db_user = User(user.username, **db[user.username])
					db_user.update_checksum()

					db[user.username]["checksum"] = db_user.checksum

					f.seek(0)
					f.truncate(0)
					f.write(json.dumps(db, ensure_ascii=False, indent="\t"))

		return user

	def get_user(self, username: str) -> User | None:
		with self.__lock:
			with open(self.__filepath, "r", encoding="utf-8") as f:
				db = json.loads(f.read())

		if username not in db:
			return None

		user = User(username, **db[username])

		if not user.verify_checksum():
			return None

		return user


def main() -> None:
	parser = argparse.ArgumentParser(
		prog="Secure Authentication",
		description="secure user authentication system using password hashing",
	)
	parser.add_argument("action", nargs="?", choices=("login", "register"), default="login")
	args = parser.parse_args()

	db = Database("users.json")

	match args.action:
		case "login":
			username = input("Username: ")
			password = getpass("Password: ", echo_char="*")

			try:
				db.login_user(username, password)
			except ValueError as e:
				print(e.args[0] if e.args else "Access denied.")
			else:
				print("Access granted.")

		case "register":
			username = input("Username: ")
			password = getpass("Password: ", echo_char="*")

			user = User.new(username, password)

			try:
				db.register_user(user)
			except KeyError as e:
				print(e.args[0] if e.args else "User already exists.")
			else:
				print("User successfully registered.")


if __name__ == "__main__":
    main()
