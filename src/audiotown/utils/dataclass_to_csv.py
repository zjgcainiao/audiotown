from dataclasses import fields
import csv
from typing import List, TypeVar, Type
from pathlib import Path

T = TypeVar("T")


def dataclasses_to_csv(
    items: List[T], dataclass_type: Type[T], filename: Path, encoding: str = "utf-8"
) -> None:
    """
    Write list of dataclass instances to CSV.
    Uses field names as headers automatically.
    """
    if not items:
        # Create empty file with header or just skip
        with open(filename, "w", newline="", encoding=encoding) as f:
            writer = csv.writer(f)
            writer.writerow([f.name for f in fields(dataclass_type)])
        return

    fieldnames = [f.name for f in fields(items[0])]

    with open(filename, "w", newline="", encoding=encoding) as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()

        for item in items:
            row = {fname: getattr(item, fname) for fname in fieldnames}
            writer.writerow(row)
