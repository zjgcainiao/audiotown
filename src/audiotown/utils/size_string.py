
def size_string(size: int) -> str:

    size_mb = size / 1024**2
    size_str = f"{size_mb/1024:.1f} GB" if size_mb > 1024 else f"{size_mb:.1f} MB"
    return size_str
    