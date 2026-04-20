
import json
from pathlib import Path
from dataclasses import dataclass, field, asdict, is_dataclass
# from typing import Optional, Tuple, Dict, List, Any, cast
from collections import Counter, defaultdict
from functools import partial
from audiotown.consts.audio.audio_format import AudioFormat
from audiotown.consts.basics.type_summary import TypeSummary
from types import MappingProxyType
import logging
from enum import Enum
from audiotown.consts.lang.detected_language import LangScriptType, DetectedLanguage
from audiotown.consts.video.video_container import VideoContainer


logger = logging.getLogger(__name__)

class AudiotownEncoder(json.JSONEncoder):
    """
    Customized Encoders that handle custom Enum classes, set and dict like objects.

    """
    def default(self, obj):

        try: 

            # 1. Manual Handle Enum AudioFormat
            if isinstance(obj, AudioFormat):
                return {
                    "suffix": obj.ext,
                    "codec_name": obj.codec_name,
                    "encoder": obj.encoder,
                    "is_lossy": obj.is_lossy,
                    "description": obj.description,
                }
            if isinstance(obj, VideoContainer):
                return {
                    "suffix": obj.suffix,
                    "muxer": obj.muxer,
                    "description": obj.description,

                }
            if isinstance(obj, DetectedLanguage):
                """
                Handle `scripts` field which is a set. set is not supported
                """
                
                data_to_save = {
                    "scripts": list(obj.scripts),  # Convert set to list here
                    "primary": obj.primary_identity.value
                }
                return data_to_save

            # Automatically handle sets
            if isinstance(obj, set):
                
                return list(obj)  
            
            # Handle other Enums
            if isinstance(obj, Enum):
                # This turns the whole messy dict into just ".avi" or "avi"
                return obj.value

            # 1. Guards: If it's a class or a function, ignore it entirely
            if isinstance(obj, type) or callable(obj):
                name = getattr(obj, "__name__", str(obj))
                logger.warning(f'this is a callable function or class that should not be here. {str(obj)}  obj.__name__: {name}')
                
                return f"<ClassOrFunction: {str(obj)}>" # Or return None to keep the JSON clean
            
            # If the object is a Path (PosixPath or WindowsPath), turn it into a string
            if isinstance(obj, Path):
                return str(obj)
            
            # 2. All dataclasses (including DuplicateGroup, TypeSummary, AudioRecord, …)
            if is_dataclass(obj) and not isinstance(obj, type):
                return asdict(obj)
            


            # 4. Collections and Proxies (The Fix for MappingProxy)
            if isinstance(obj, (Counter, defaultdict, MappingProxyType)):
                return dict(obj)
            
            if isinstance(obj, TypeSummary):
                return {"count": obj.count, "size_bytes": obj.size_bytes}
                # return obj.to_dict() if hasattr(obj, "to_dict") else vars(obj)
            
            # 5. The Catch-all (Safe version)
            # if hasattr(obj, "__dict__"):
            #     # Cast vars to a dict to ensure we aren't passing a mappingproxy back
            #     return vars(obj)
            # Only use vars() on things that are definitely not internal Python junk
            if hasattr(obj, "__dict__") and not str(type(obj)).startswith("<class 'type"):
                return dict(vars(obj))

            return super().default(obj)


        except Exception as e:
            logger.error(f"DEBUG: Encoder failing on object: {obj} (Type: {type(obj)})")
            return super().default(obj)
