# Symbol is a helper type that contains the name of a variable, its ast id, and its parent scope id
from dataclasses import dataclass

from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from .types import Type


@dataclass(slots=True)
class Symbol:
    """Represents a symbol. A symbol is a name for a variable, its ast id, and its parent scope id"""

    name: str
    ast_id: int
    parent_scope_id: int
    type: Optional["Type"] = None
