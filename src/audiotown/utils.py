from pathlib import Path
from typing import Optional
from audiotown.logger import logger
import unicodedata
from typing import Optional,Union


def safe_division(n1:Union[int, float], n2:Union[int, float])-> float:
    try:
        result = float(n1/n2)
        return result
    except ZeroDivisionError:
        return float(0.0)

    
def to_int(val, default=0) -> int:
    """Safely converts a value to integer, returning default on failure."""
    try:
        # We strip() in case there are hidden spaces like " 2024 "
        return int(str(val).strip())
    except (ValueError, TypeError):
        return default

def find_external_cover(folder_path: Path) -> Optional[Path]:
    valid_names = {"cover", "folder", "front", "album"}
    valid_extensions = {".jpg", ".jpeg", ".png"}
    if not folder_path or not Path(folder_path).is_dir:
        return None
    try:
        for file in folder_path.iterdir():
            if file.is_file():
                if (
                    file.stem.lower() in valid_names
                    and file.suffix.lower() in valid_extensions
                ):
                    return file
    except PermissionError:
        return None
    except Exception:
        return None
    return None


def sanitize_metadata(text: str) -> str:
    """Normalizes unicode and standardizes punctuation for metadata."""
    if not text:
        return ""

    # 1. Unicode Normalization (converts 'é' combined from 'e'+'´' into a single char)
    text = unicodedata.normalize("NFC", text)

    # 2. Quote Standardization (The "Senior" move)
    # This replaces all 'smart' quotes, backticks, and slanted quotes with standard ones
    quote_map = {
        "“": '"',
        "”": '"',  # Smart double quotes
        "‘": "'",
        "’": "'",  # Smart single quotes
        "‹": "'",
        "›": "'",  # French/other pointers
        "«": '"',
        "»": '"',
        "＂": '"',  # Full-width quotes
        "`": "'",  # Backticks
    }

    for bad_char, good_char in quote_map.items():
        text = text.replace(bad_char, good_char)

    # 3. Cleanup Whitespace
    return text

# -- create blocks, sections lines for terminal output --
def div_blocks(number: int, divider: str = "= ") -> str:
    """Generates a repeating block of characters."""
    count = number if number > 0 else 5
    return (divider * count).strip()


def div_section_line(message: str = "", level: int = 1) -> str:
    """Creates a centered section line with consistent padding."""
    match level:
        case 1:
            blocks = div_blocks(10, "= ")
        case 2:
            blocks = div_blocks(5, "- ")
        case 3:
            blocks = div_blocks(5, "*")
        case _:
            blocks = div_blocks(10, "= ")
    blocks = blocks.strip()
    if not message:
        return blocks
    return f"{blocks} {message.strip()} {blocks}"


def format_section(title: str, data: dict) -> str:
    blocks = div_blocks(3, "*")
    title_line = f"{blocks} {title} {blocks}"
    if not data:
        return title_line + "\n(empty)"

    # stringify keys/values; you can also prettify keys here if you want
    items = [(str(k), data[k]) for k in data.keys()]
    width = max(len(k) for k, _ in items) + 2

    lines = [title_line]
    for k, v in items:
        lines.append(f" {k:<{width}}: {v}")
    lines.append(f"{blocks} End of {title} {blocks}")
    return "\n".join(lines)

