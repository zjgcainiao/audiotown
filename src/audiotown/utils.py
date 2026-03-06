from pathlib import Path
from typing import Optional
from audiotown.logger import logger
import unicodedata
from typing import Optional

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
