import os
from typing import ClassVar, Iterator

from secure_authentication import User, get_db, prompt_login

type StrOrBytesPath = str | bytes | os.PathLike


class Permission:
	READ: ClassVar[int] = 1 << 0
	WRITE: ClassVar[int] = 1 << 1
	DELETE: ClassVar[int] = 1 << 2

	def __init__(self, **kwargs) -> None:
		self.__value = 0

		for k, v in kwargs.items():
			setattr(self, k, v)

	@property
	def value(self) -> int:
		return self.__value

	@value.setter
	def value(self, new_value: int) -> None:
		self.__value = new_value

	@property
	def read(self) -> bool:
		return (self.value & self.__class__.READ) == self.__class__.READ

	@read.setter
	def read(self, new_value: bool) -> None:
		if new_value:
			self.value += self.__class__.READ
		else:
			self.value -= self.__class__.READ

	@property
	def write(self) -> bool:
		return (self.value & self.__class__.WRITE) == self.__class__.WRITE

	@write.setter
	def write(self, new_value: bool) -> None:
		if new_value:
			self.value += self.__class__.WRITE
		else:
			self.value -= self.__class__.WRITE

	@property
	def delete(self) -> bool:
		return (self.value & self.__class__.DELETE) == self.__class__.DELETE

	@delete.setter
	def delete(self, new_value: bool) -> None:
		if new_value:
			self.value += self.__class__.DELETE
		else:
			self.value -= self.__class__.DELETE

	@classmethod
	def from_value(cls, value: int) -> Permission:
		self = cls()
		self.value = value
		return self

	def has(self, permission: Permission | int | str) -> bool:
		if isinstance(permission, self.__class__):
			for perm, value in permission:
				if not value:
					continue

				if not getattr(self, perm):
					return False

			return True
		elif isinstance(permission, int):
			return (self.value & permission) == permission
		elif isinstance(permission, str):
			return getattr(self, permission)

		return False

	def __eq__(self, other: object) -> bool:
		return isinstance(other, self.__class__) and self.value == other.value

	def __hash__(self) -> int:
		return hash(self.value)

	def __and__(self, other) -> Permission:
		if isinstance(other, self.__class__):
			return self.__class__.from_value(self.value & other.value)
		elif isinstance(other, int):
			return self.__class__.from_value(self.value & other)

		raise TypeError

	def __or__(self, other) -> Permission:
		if isinstance(other, self.__class__):
			return self.__class__.from_value(self.value | other.value)
		elif isinstance(other, int):
			return self.__class__.from_value(self.value | other)

		raise TypeError

	def __add__(self, other: object) -> Permission:
		return self | other

	def __sub__(self, other: object) -> Permission:
		if isinstance(other, self.__class__):
			return self.__class__.from_value(self.value & ~other.value)
		elif isinstance(other, int):
			return self.__class__.from_value(self.value & ~other)

		raise TypeError

	def __invert__(self) -> Permission:
		return self.__class__.from_value(~self.value)

	def __iter__(self) -> Iterator[tuple[str, bool]]:
		for name in ("read", "write", "delete"):
			yield (name, getattr(self, name))

	def __repr__(self) -> str:
		return f"<{self.__class__.__name__} value={self.value}>"


class FileObject:
	def __init__(self, filepath: StrOrBytesPath) -> None:
		self.__filepath = os.path.normpath(filepath)

		if os.path.exists(self.__filepath) and not os.path.isfile(self.__filepath):
			raise ValueError("filepath cannot point to directory")

	@property
	def filepath(self) -> StrOrBytesPath:
		return self.__filepath

	@property
	def filename(self) -> StrOrBytesPath:
		return os.path.basename(self.__filepath)

	@property
	def dirname(self) -> StrOrBytesPath:
		return os.path.dirname(self.__filepath)

	def _read(self, not_found_ok: bool = False) -> bytes:
		try:
			with open(self.__filepath, "rb") as f:
				data = f.read()
		except FileNotFoundError:
			return b""

		return data

	def _write(self, data: bytes) -> None:
		os.makedirs(self.dirname, exist_ok=True)

		with open(self.__filepath, "wb") as f:
			f.write(data)

	def _delete(self, not_found_ok: bool = False) -> None:
		if not_found_ok and not os.path.isfile(self.__filepath):
			return

		os.remove(self.__filepath)


class AccessController:
	def __init__(self) -> None:
		pass

	def get_permissions(self, user: User | None = None) -> Permission:
		if user is None:
			return Permission(read=True)

		if user.is_admin():
			return Permission(read=True, write=True, delete=True)

		return Permission(read=True, write=True)

	def has_permission(self, permission: Permission | int | str, user: User | None = None) -> bool:
		permissions = self.get_permissions(user)
		return permissions.has(permission)

	def read_file(self, file: FileObject, user: User | None = None) -> bytes:
		if not self.has_permission(Permission.READ, user):
			raise PermissionError("user has no access to read")

		return file._read(True)

	def write_file(self, file: FileObject, data: bytes, user: User | None = None) -> None:
		if not self.has_permission(Permission.WRITE, user):
			raise PermissionError("user has no access to write")

		return file._write(data)

	def delete_file(self, file: FileObject, user: User | None = None) -> None:
		if not self.has_permission(Permission.DELETE, user):
			raise PermissionError("user has no access to delete")

		return file._delete(True)


def main() -> None:
	access_controller = AccessController()

	db = get_db()
	user = prompt_login(db)

	filename = ""

	while filename != ".exit":
		_filename = input("Filepath: ")

		if _filename != "":
			filename = _filename

		file = FileObject(filename)

		action = input("Action (read/write/delete): ").lower()

		while action not in ("read", "write", "delete"):
			print("Invalid action")
			action = input("Action (read/write/delete): ").lower()

		if action == "read":
			print(access_controller.read_file(file, user))
		elif action == "write":
			data = input("\n").encode("utf-8")

			access_controller.write_file(file, data, user)
		elif action == "delete":
			access_controller.delete_file(file, user)


if __name__ == "__main__":
	main()
