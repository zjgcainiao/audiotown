
import json
from pathlib import Path
from dataclasses import dataclass, field, asdict, is_dataclass
from typing import Optional, Tuple, Dict, List, Any, cast, Set, DefaultDict
from collections import Counter, defaultdict
from functools import partial
from .audio_format import AudioFormat
from .type_summary import TypeSummary

class AudiotownEncoder(json.JSONEncoder):
    def default(self, obj):
        # If the object is a Path (PosixPath or WindowsPath), turn it into a string
        if isinstance(obj, Path):
            return str(obj)
        # 2. All dataclasses (including DuplicateGroup, TypeSummary, AudioRecord, …)
        if is_dataclass(obj) and not isinstance(obj, type):
            return asdict(obj)
        if isinstance(obj, AudioFormat):
            return {
                "ext": obj.ext,
                "codec_name": obj.codec_name,
                "encoder": obj.encoder,
                "is_lossy": obj.is_lossy,
                "description": obj.description,
            }
        if isinstance(obj, (Counter, defaultdict)):
            return dict(obj)
        if isinstance(obj, TypeSummary):
            return {"count": obj.count, "size_bytes": obj.size_bytes}
            # return obj.to_dict() if hasattr(obj, "to_dict") else vars(obj)

        if hasattr(obj, "__dict__"):
            # print(f"obj: {obj}. type: {type(obj)}")
            return vars(obj)
        # Otherwise, let the standard encoder handle it
        return super().default(obj)