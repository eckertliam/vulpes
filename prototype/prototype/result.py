from typing import Generic, List, TypeVar, Optional

from prototype.errors import VulpesError

T = TypeVar("T")
U = TypeVar("U")


class Result(Generic[T]):
    def __init__(self, value: Optional[T] = None, errors: Optional[List[VulpesError]] = None):
        self._value = value
        self._errors = errors or []

    @staticmethod
    def ok(value: T) -> "Result[T]":
        return Result(value=value)

    @staticmethod
    def err(errors: List[VulpesError]) -> "Result[T]":
        return Result(errors=errors)

    def is_ok(self) -> bool:
        return self._value is not None and not self._errors

    def is_err(self) -> bool:
        return not self.is_ok()

    def unwrap(self) -> T:
        if self.is_err():
            raise ValueError(f"Called unwrap on an Err result: {self._errors}")
        return self._value  # type: ignore

    def unwrap_err(self) -> List[VulpesError]:
        if self.is_ok():
            raise ValueError("Called unwrap_err on an Ok result")
        return self._errors
