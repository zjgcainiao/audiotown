from pathlib import Path
from audiotown.logger import logger
import unicodedata
from typing import Optional, Union
from datetime import datetime

# def extract_year_from_str(value: str) -> Optional[int]:
#     """
#     Try to extract a 4-digit year from various messy formats.
#     Returns None if no valid year found or out of reasonable range.
#     """
#     if not value or not isinstance(value, str):
#         return None

#     current_year = datetime.now().year

#     # Try common patterns
#     for fmt in [
#         "%Y", "%y", "%Y-%m-%d", "%d/%m/%Y", "%m/%d/%Y",
#         "%Y.%m.%d", "%d.%m.%Y", "%Y %m %d", "%b %d, %Y"
#     ]:
#         try:
#             dt = datetime.strptime(value.strip(), fmt)
#             year = dt.year
#             if 1900 <= year <= current_year + 5:
#                 return year
#         except ValueError:
#             continue

#     # Fallback: look for any 4 consecutive digits in the string
#     import re
#     match = re.search(r'\b(19\d{2}|20\d{2})\b', value)
#     if match:
#         year = int(match.group(1))
#         if 1900 <= year <= current_year + 5:
#             return year

#     return None


# def duration_string(duration: float) -> str:
#     """genrate a human friendly format based on duration in seconds.
#         Output will look like 20 mins, 30.5 hours, 30.0 days  or 1.2 years
#     Args:
#         duration (float): duration in seconds

#     Returns:
#         str: the human friendly string format
#     """
#     SECS_PER_HOUR = 60 * 60
#     SECS_PER_DAY = 24 * SECS_PER_HOUR

#     if duration <= 0:
#         return ""
#     elif duration < SECS_PER_HOUR:
#         string = f"{duration/ SECS_PER_HOUR:,.1f} mins"
#     elif duration < 100 * SECS_PER_HOUR:
#         string = f"{duration/ SECS_PER_HOUR:,.1f} hours"
#     elif duration < 400 * SECS_PER_DAY:
#         string = f"{duration/ SECS_PER_DAY:,.1f} days"
#     else:
#         string = f"{duration/ SECS_PER_DAY:,.1f} years"
#     return string


# def size_string(size: int) -> str:

#     size_mb = size / 1024**2
#     size_str = f"{size_mb/1024:.1f} GB" if size_mb > 1024 else f"{size_mb:.1f} MB"
#     return size_str


# def safe_division(n1: Union[int, float], n2: Union[int, float]) -> Optional[float]:
#     try:
#         result = float(n1 / n2)
#         return result
#     except ZeroDivisionError:
#         return float(0.0)
#     except Exception:
#         return None


# def to_int(val, default=0) -> int:
#     """Safely converts a value to integer, returning default on failure."""
#     try:
#         # We strip() in case there are hidden spaces like " 2024 "
#         return int(str(val).strip())
#     except (ValueError, TypeError):
#         return default


# def find_external_cover(folder_path: Path) -> Optional[Path]:
#     valid_names = {"cover", "folder", "front", "album"}
#     valid_extensions = {".jpg", ".jpeg", ".png"}
#     if not folder_path or not Path(folder_path).is_dir:
#         return None
#     try:
#         for file in folder_path.iterdir():
#             if file.is_file():
#                 if (
#                     file.stem.lower() in valid_names
#                     and file.suffix.lower() in valid_extensions
#                 ):
#                     return file
#     except PermissionError:
#         return None
#     except Exception:
#         return None
#     return None


# def sanitize_metadata(text: str) -> str:
#     """Normalizes unicode and standardizes punctuation for metadata."""
#     if not text:
#         return ""

#     # 1. Unicode Normalization (converts 'é' combined from 'e'+'´' into a single char)
#     text = unicodedata.normalize("NFC", text)

#     # 2. Quote Standardization (The "Senior" move)
#     # This replaces all 'smart' quotes, backticks, and slanted quotes with standard ones
#     quote_map = {
#         "“": '"',
#         "”": '"',  # Smart double quotes
#         "‘": "'",
#         "’": "'",  # Smart single quotes
#         "‹": "'",
#         "›": "'",  # French/other pointers
#         "«": '"',
#         "»": '"',
#         "＂": '"',  # Full-width quotes
#         "`": "'",  # Backticks
#     }

#     for bad_char, good_char in quote_map.items():
#         text = text.replace(bad_char, good_char)

#     # 3. Cleanup Whitespace
#     return text


# -- create blocks, sections lines for terminal output --
# def div_blocks(number: int, divider: str = "= ") -> str:
#     """Generates a repeating block of characters."""
#     count = number if number > 0 else 5
#     return (divider * count).strip()


# def div_section_line(message: str = "", level: int = 1) -> str:
#     """Creates a centered section line with consistent padding."""
#     match level:

#         # heading 1 style
#         case 1:
#             blocks = div_blocks(10, "= ")
#         case 2:
#             blocks = div_blocks(5, "- ")
#         case 3:
#             blocks = div_blocks(3, "*")
#         case _:
#             blocks = div_blocks(10, "= ")
#     blocks = blocks.strip()
#     if not message:
#         return blocks
#     return f"{blocks} {message.strip()} {blocks}"


# def format_section(title: str, data: dict) -> str:
#     blocks = div_blocks(3, "*")
#     title_line = f"{blocks} {title} {blocks}"
#     if not data:
#         return title_line + "\n(empty)"

#     # stringify keys/values; you can also prettify keys here if you want
#     items = [(str(k), data[k]) for k in data.keys()]
#     width = max(len(k) for k, _ in items) + 2

#     lines = [title_line]
#     for k, v in items:
#         lines.append(f" {k:<{width}}: {v}")
#     lines.append(f"{blocks} End of {title} {blocks}")
#     return "\n".join(lines)


# from dataclasses import fields
# import csv
# from typing import List, TypeVar, Type

# T = TypeVar("T")


# def dataclasses_to_csv(
#     items: List[T], dataclass_type: Type[T], filename: Path, encoding: str = "utf-8"
# ) -> None:
#     """
#     Write list of dataclass instances to CSV.
#     Uses field names as headers automatically.
#     """
#     if not items:
#         # Create empty file with header or just skip
#         with open(filename, "w", newline="", encoding=encoding) as f:
#             writer = csv.writer(f)
#             writer.writerow([f.name for f in fields(dataclass_type)])
#         return

#     fieldnames = [f.name for f in fields(items[0])]

#     with open(filename, "w", newline="", encoding=encoding) as f:
#         writer = csv.DictWriter(f, fieldnames=fieldnames)
#         writer.writeheader()

#         for item in items:
#             row = {fname: getattr(item, fname) for fname in fieldnames}
#             writer.writerow(row)
