from typing import ClassVar, Iterator

from secure_authentication import User


class Permission():
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

	def __add__(self, other) -> Permission:
		return self | other

	def __sub__(self, other) -> Permission:
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

	def __gte__(self, other) -> bool:
		if isinstance(other, self.__class__):
			for (permission, value) in other:
				if not value:
					continue

				if not getattr(self, permission):
					return False

			return True
		elif isinstance(other, int):
			return (self & other) == other
		elif isinstance(other, str):
			return getattr(self, other)

		raise TypeError

	def __repr__(self) -> str:
		return f"<{self.__class__.__name__} value={self.value}>"


class FileObject():
	pass


class AccessController():
	def __init__(self) -> None:
		pass

	def get_permissions(self, user: User | None = None) -> Permission:
		if user is None:
			return Permission(read=True)

		if user.is_admin():
			return Permission(read=True, write=True, delete=True)

		return Permission(read=True, write=True)

	def has_permission(self, permission: Permission, user: User | None = None) -> bool:
		permissions = self.get_permissions(user)

		for (perm, value) in permission:
			if not value:
				continue

			if not getattr(permissions, perm):
				return False

		return True


def main() -> None:
	access_controller = AccessController()

	permissions = Permission(read=True)
	permissions.write = True

	try_permissions = Permission(read=True, write=True)

	print(access_controller.has_permission(try_permissions, user))


if __name__ == "__main__":
	main()
