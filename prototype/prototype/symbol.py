# Symbol is a helper type that contains the name of a variable, its ast id, and its parent scope id
from dataclasses import dataclass
from typing import Optional, Type


@dataclass
class Symbol:
    name: str
    ast_id: int
    parent_scope_id: int
    type: Optional[Type] = None
