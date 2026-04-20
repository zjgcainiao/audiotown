LANGUAGE_MAP = {
    # English variants
    "eng": "eng",
    "en": "eng",
    "english": "eng",
    "en-US": "eng",
    "en-GB": "eng",
    
    # Spanish
    "spa": "spa",
    "es": "spa",
    "spanish": "spa",
    "es-ES": "spa",
    "es-MX": "spa",
    
    # French
    "fra": "fra",
    "fre": "fra",  # Alternative code
    "fr": "fra",
    "french": "fra",
    "fr-FR": "fra",
    "fr-CA": "fra",
    
    # German
    "deu": "deu",
    "ger": "deu",
    "de": "deu",
    "german": "deu",
    "de-DE": "deu",
    
    # Italian
    "ita": "ita",
    "it": "ita",
    "italian": "ita",
    "it-IT": "ita",
    
    # Portuguese
    "por": "por",
    "pt": "por",
    "portuguese": "por",
    "pt-PT": "por",
    "pt-BR": "por",
    
    # Russian
    "rus": "rus",
    "ru": "rus",
    "russian": "rus",
    "ru-RU": "rus",
    
    # Arabic
    "ara": "ara",
    "ar": "ara",
    "arabic": "ara",
    "ar-SA": "ara",
    "ar-EG": "ara",
    
    # Chinese
    "zho": "zho",
    "chi": "zho",
    "zh": "zho",
    "chinese": "zho",
    "zh-CN": "zho",  # Simplified
    "zh-TW": "zho",  # Traditional
    
    # Japanese
    "jpn": "jpn",
    "ja": "jpn",
    "japanese": "jpn",
    "ja-JP": "jpn",
    
    # Korean
    "kor": "kor",
    "ko": "kor",
    "korean": "kor",
    "ko-KR": "kor",
    
    # Hindi
    "hin": "hin",
    "hi": "hin",
    "hindi": "hin",
    "hi-IN": "hin",
    
    # Dutch
    "nld": "nld",
    "dut": "nld",
    "nl": "nld",
    "dutch": "nld",
    "nl-NL": "nld",
    
    # Turkish
    "tur": "tur",
    "tr": "tur",
    "turkish": "tur",
    "tr-TR": "tur",
    
    # Polish
    "pol": "pol",
    "pl": "pol",
    "polish": "pol",
    "pl-PL": "pol",
    
    # Swedish
    "swe": "swe",
    "sv": "swe",
    "swedish": "swe",
    "sv-SE": "swe",
    
    # Greek
    "ell": "ell",
    "gre": "ell",
    "el": "ell",
    "greek": "ell",
    "el-GR": "ell",
    
    # Hebrew
    "heb": "heb",
    "he": "heb",
    "iw": "heb",  # Older code
    "hebrew": "heb",
    "he-IL": "heb",
    
    # Thai
    "tha": "tha",
    "th": "tha",
    "thai": "tha",
    "th-TH": "tha",
    
    # Vietnamese
    "vie": "vie",
    "vi": "vie",
    "vietnamese": "vie",
    "vi-VN": "vie",
    
    # Indonesian
    "ind": "ind",
    "id": "ind",
    "indonesian": "ind",
    "id-ID": "ind",
    
    # Undefined/Unknown
    "und": None,
    "unknown": None,
    "": None,
    None: None,
}

def map_language(lang_code):
    lang_map = LANGUAGE_MAP
    return lang_map.get(lang_code.lower(), lang_code.lower())





# Create a separate mapping for display names
LANG_DISPLAY_NAMES = {
    "eng": "English",
    "spa": "Spanish",
    "fra": "French",
    "deu": "German",
    "ita": "Italian",
    "por": "Portuguese",
    "rus": "Russian",
    "ara": "Arabic",
    "jpn": "Japanese",
    "kor": "Korean",
    "zho": "Chinese",
    "hin": "Hindi",
    "nld": "Dutch",
    "tur": "Turkish",
    "pol": "Polish",
    "swe": "Swedish",
    "ell": "Greek",
    "heb": "Hebrew",
    "tha": "Thai",
    "vie": "Vietnamese",
    "ind": "Indonesian",
}

