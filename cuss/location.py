from dataclasses import dataclass

@dataclass
class Location:
    line: int
    column: int

    def __str__(self):
        return f"{self.line}:{self.column}"
    
