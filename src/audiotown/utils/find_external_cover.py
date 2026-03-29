from pathlib import Path
from typing import Optional, Union


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