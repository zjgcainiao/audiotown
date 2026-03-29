import unicodedata

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
