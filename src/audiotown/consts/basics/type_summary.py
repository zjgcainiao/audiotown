from dataclasses import dataclass, field
from pathlib import Path
from typing import List

@dataclass(slots=True)
class TypeSummary:
    count: int = 0
    size_bytes: int = 0

    def __add__(self, other: "TypeSummary") -> "TypeSummary":
        """Magic method to allow: total = summary_a + summary_b"""
        if not isinstance(other, TypeSummary):
            return self
        return TypeSummary(
            count=self.count + other.count,
            size_bytes=self.size_bytes + other.size_bytes,
        )


@dataclass(slots=True)
class Type2Summary:
    count: int = 0
    size_bytes: int = 0
    files: List[Path] = field(default_factory=list)
