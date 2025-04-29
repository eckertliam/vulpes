# Passes are used to transform and validate the AST
# This is the base class for all passes
from abc import ABC, abstractmethod
from typing import Dict, Optional, Union

from .errors import CussError, NameResolutionError, TypeInferenceError
from .parser import (
    ArrayTypeAnnotation,
    Declaration,
    EnumDecl,
    FnDecl,
    FunctionTypeAnnotation,
    If,
    ImplDecl,
    Loop,
    NamedTypeAnnotation,
    Program,
    Statement,
    StructDecl,
    TupleTypeAnnotation,
    TypeAliasDecl,
    TypeAnnotation,
    VarDecl,
    While,
    Tuple,
)
from .types import (
    ArrayType,
    EnumType,
    FunctionType,
    StructType,
    TupleType,
    Type,
    TypeVar,
)


class Pass(ABC):
    @abstractmethod
    def run(self, program: Program) -> Program:
        pass
