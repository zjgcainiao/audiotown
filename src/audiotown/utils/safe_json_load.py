import json
import logging

logger = logging.getLogger(__name__)


def safe_json_load(raw_str: str | None, fallback: dict|None = None) -> dict:
    """Ensures the app doesn't crash if DB content is corrupt."""
    if fallback is None:
        fallback = {}
    if not raw_str:
        return fallback
    try:
        return json.loads(raw_str)
    except (json.JSONDecodeError, TypeError):
        # Log the error, but keep the dashboard alive
        logger.error(f"Corruption detected in JSON field: {raw_str}")
        return fallback