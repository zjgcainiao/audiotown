from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum, StrEnum
from pathlib import Path
from typing import Optional
from collections import Counter

class LangScriptType(Enum):
    HAN = "HAN"
    HIRAGANA = "HIRAGANA"
    KATAKANA = "KATAKANA"
    ARABIC = "ARABIC"
    HANGUL = "HANGUL"
    LATIN = "LATIN"
    CYRILLIC = "CYRILLIC" # Added for Russian/Bulgarian/etc.
    GREEK = "GREEK"

class LangTag(StrEnum):
    LATIN = "Latin"
    JAPANESE = "Japanese"
    KOREAN = "Korean"
    CHINESE = "Chinese"
    CYRILLIC = "Cyrillic"
    ARABIC = "Arabic"
    GREEK = "Greek"
    MULTILINGUAL = "Multilingual"
    UNKNOWN = "Unknown"

SIMPLIFIED_ONLY = set("汉语国门书车云万东龙后发叶听一二三四五六七八九十")
TRADITIONAL_ONLY = set("漢語國門書車雲萬東龍後發葉聽")

GERMAN_HINTS = set("äöüß")
FRENCH_HINTS = set("àâçéèêëîïôùûüÿœæ")
ENGLISH_COMMON = {"the", "and", "is", "are", "of", "to", "in", "that", "it", "for"}

# Mapping of Unicode ranges to Script Types
SCRIPT_RANGES = {
    LangScriptType.HIRAGANA: range(0x3040, 0x30A0),
    LangScriptType.KATAKANA: range(0x30A0, 0x3100),
    LangScriptType.HAN: range(0x4E00, 0x9FFF),
    LangScriptType.ARABIC: range(0x0600, 0x0700), # Basic Arabic block
    LangScriptType.HANGUL: range(0xAC00, 0xD7B0),
    LangScriptType.CYRILLIC: range(0x0400, 0x0530),
    LangScriptType.GREEK: range(0x0370, 0x0400),
    # Latin includes Basic, Supplement, and Extended A/B
    LangScriptType.LATIN: range(0x0041, 0x0250), 
}

@dataclass(slots=True, frozen=True)
class DetectedLanguage:
    """
    Detect the language used based on the text script types in an audio file.
        - file: the absolute file path
        - script: a set of LangScriptType detected via its Lang's Unicode
    """

    # assigned_tags: tuple[str, ...]
    # detected_scripts: tuple[LangScriptType, ...]
    scripts: set[LangScriptType] = field(default_factory=set)
    # language_used: str
    # is_ambiguous: bool = False
    notes: str = ""

    @classmethod
    def from_text(cls, text: str):
        """Factory method to create instance directly from string."""
        if not text or not text.strip():
            return cls()
        
        found:set[LangScriptType] = set()
        # Clean text once
        clean_text = "".join(c for c in text if not (c.isspace() or c.isdigit()))
        
        for char in clean_text:
            cp = ord(char)
            for script, r in SCRIPT_RANGES.items():
                if cp in r:
                    found.add(script)
                    break 
        return cls(scripts=found)

    @property
    def primary_identity(self) -> LangTag:
        """Maps detected scripts to a clean UI-friendly LangTag."""
        if not self.scripts:
            return LangTag.UNKNOWN
        
        # 1. Priority: Multi-script check
        if self.is_ambiguous:
            return LangTag.MULTILINGUAL

        # 2. Priority: Complex Asian Scripts
        if self.scripts & {LangScriptType.HIRAGANA, LangScriptType.KATAKANA}:
            return LangTag.JAPANESE
        if LangScriptType.HANGUL in self.scripts:
            return LangTag.KOREAN
        if LangScriptType.HAN in self.scripts:
            return LangTag.CHINESE
            
        # 3. Direct Mappings
        mapping = {
            LangScriptType.CYRILLIC: LangTag.CYRILLIC,
            LangScriptType.GREEK: LangTag.GREEK,
            LangScriptType.ARABIC: LangTag.ARABIC,
            LangScriptType.LATIN: LangTag.LATIN,
        }

        for script, tag in mapping.items():
            if script in self.scripts:
                return tag
                
        return LangTag.UNKNOWN

    @property
    def is_ambiguous(self) -> bool:
        """
        True if the text contains multiple competing script families.
        Note: We don't count Japanese components as competing.
        """
        if not self.scripts:
            return False
            
        # Create a copy to manipulate
        test_scripts = self.scripts.copy()
        
        # Consolidate Japanese: If any JP scripts exist, treat as one 'unit'
        jp_scripts = {LangScriptType.HIRAGANA, LangScriptType.KATAKANA}
        if test_scripts & jp_scripts:
            test_scripts -= jp_scripts
            test_scripts.add(LangScriptType.HAN) # Treat the whole block as Han/JP
            
        return len(test_scripts) > 1
    

    @classmethod
    def detect_scripts(cls, text: str) -> set[LangScriptType]:
        if not text or not text.strip():
            return set()

        scripts = set()
        # Filter out noise once
        chars = [ord(ch) for ch in text if not (ch.isspace() or ch.isdigit())]

        for cp in chars:
            for script, r in SCRIPT_RANGES.items():
                if cp in r:
                    scripts.add(script)
                    break # Move to next character once match found
        
        return scripts
    # @classmethod
    # def detect_scripts(cls, text: str) -> set[LangScriptType]:
    #     scripts: set[LangScriptType] = set()
    #     if not text or not text.strip():
    #         return set()
    #     text = text.casefold().strip()
    #     for ch in text:
    #         if ch.isspace() or ch.isdigit():
    #             continue
    #         cp = ord(ch)

    #         if 0x3040 <= cp <= 0x309F:
    #             scripts.add(LangScriptType.HIRAGANA)
    #         elif 0x30A0 <= cp <= 0x30FF:
    #             scripts.add(LangScriptType.KATAKANA)
    #         elif 0x4E00 <= cp <= 0x9FFF:
    #             scripts.add(LangScriptType.HAN)
    #         elif 0x0600 <= cp <= 0x06FF or 0x0750 <= cp <= 0x077F or 0x08A0 <= cp <= 0x08FF:
    #             scripts.add(LangScriptType.ARABIC)
    #         elif 0xAC00 <= cp <= 0xD7AF:
    #             scripts.add(LangScriptType.HANGUL)
    #         elif 0x0041 <= cp <= 0x005A or 0x0061 <= cp <= 0x007A or 0x00C0 <= cp <= 0x024F:
    #             scripts.add(LangScriptType.LATIN)

    #     return scripts

    # @classmethod
    # def classify_file_language(cls, text: str, file: Optional[Path]=None) -> DetectedLanguage:
    #     scripts = cls.detect_scripts(text)
    #     assigned_tags: set[LangTag] =set()
    #     notes: str = ""
    #     is_ambiguous: bool = False

    #     has_hiragana: bool = LangScriptType.HIRAGANA in scripts
    #     has_katakana: bool = LangScriptType.KATAKANA in scripts
    #     has_han: bool = LangScriptType.HAN in scripts
    #     has_arabic: bool = LangScriptType.ARABIC in scripts
    #     has_hangul: bool = LangScriptType.HANGUL in scripts
    #     has_latin: bool = LangScriptType.LATIN in scripts

    #     if has_arabic:
    #         assigned_tags.add(LangTag.ARA)

    #     if has_hiragana or has_katakana:
    #         assigned_tags.add(LangTag.JPN)
    #         if has_han:
    #             assigned_tags.add(LangTag.HAN)
    #         language_used = "Japanese"
    #         notes = "Kana detected, so the file is marked as Japanese."
    #         return DetectedLanguage(
    #             file=file,
    #             assigned_tags=tuple(assigned_tags),
    #             detected_scripts=tuple(sorted(scripts, key=lambda s: s.value)),
    #             language_used=language_used,
    #             is_ambiguous=False,
    #             notes=notes,
    #         )

    #     if has_han:
    #         assigned_tags.add(LangTag.HAN)
    #         language_used = "Japanese/Chinese Han text"
    #         is_ambiguous = True
    #         notes = "Han characters detected without Hiragana/Katakana, so this is not safely marked as JPN."
    #         return DetectedLanguage(
    #             file=file,
    #             assigned_tags=tuple(assigned_tags),
    #             detected_scripts=tuple(sorted(scripts, key=lambda s: s.value)),
    #             language_used=language_used,
    #             is_ambiguous=is_ambiguous,
    #             notes=notes,
    #         )

    #     if has_hangul:
    #         assigned_tags.add(LangTag.KOR)
    #         return DetectedLanguage(
    #             file=file,
    #             assigned_tags=tuple(assigned_tags),
    #             detected_scripts=tuple(sorted(scripts, key=lambda s: s.value)),
    #             language_used="Korean",
    #             is_ambiguous=False,
    #             notes="Hangul detected.",
    #         )

    #     if has_arabic:
    #         return DetectedLanguage(
    #             file=file,
    #             assigned_tags=tuple(assigned_tags),
    #             detected_scripts=tuple(sorted(scripts, key=lambda s: s.value)),
    #             language_used="Arabic",
    #             is_ambiguous=False,
    #             notes="Arabic script detected.",
    #         )

    #     if has_latin:
    #         assigned_tags.add(LangTag.LATN)
    #         return DetectedLanguage(
    #             file=file,
    #             assigned_tags=tuple(assigned_tags),
    #             detected_scripts=tuple(sorted(scripts, key=lambda s: s.value)),
    #             language_used="Latin-script text",
    #             is_ambiguous=True,
    #             notes="Latin script detected (western)..",
    #         )

    #     assigned_tags.add(LangTag.UNK)
    #     return DetectedLanguage(
    #         file=file,
    #         assigned_tags=tuple(assigned_tags),
    #         detected_scripts=tuple(sorted(scripts, key=lambda s: s.value)),
    #         language_used="Unknown",
    #         is_ambiguous=True,
    #         notes="No supported lang script was detected.",
    #     )
