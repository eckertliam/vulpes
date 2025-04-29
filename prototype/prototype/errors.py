# Error handling
from .parser import Program


class CussError(Exception):
    def __init__(self, message: str, line: int, ast_id: int) -> None:
        super().__init__(f"[Line {line}] {message}")
        self.message = message
        self.line = line
        self.ast_id = ast_id

    def __str__(self) -> str:
        return f"[Line {self.line}] {self.message}"

    def report(self, program: Program) -> None:
        # get the declaration of the node
        decl = program.get_decl(self.ast_id)
        if decl is None:
            raise RuntimeError(f"Declaration not found for ast_id: {self.ast_id}")
        # print the error
        print(f"Error: {self}")
        # get the span of the declaration
        span = decl.get_span()
        # get the source code
        source = program.source
        if source is None:
            raise RuntimeError(f"Source code not found for ast_id: {self.ast_id}")
        # split the source code into lines
        lines = source.splitlines()
        # print the lines with the error
        for i in range(span[0], span[1]):
            if i == self.line:
                print(f"{i} | > {lines[i]}")
            else:
                print(f"{i} |   {lines[i]}")


# Cannot infer type
class TypeInferenceError(CussError):
    pass


# Cannot resolve name
class NameResolutionError(CussError):
    pass
