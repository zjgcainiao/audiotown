from dataclasses import dataclass

@dataclass(slots=True)
class LangScriptCounts:
    latin: int = 0
    cjk: int = 0
    hiragana: int = 0
    katakana: int = 0
    hangul: int = 0
    cyrillic: int = 0
    digit: int = 0
    whitespace: int = 0
    punctuation: int = 0
    other: int = 0

    @property
    def letters_total(self) -> int:
        return self.latin + self.cjk + self.hiragana + self.katakana + self.hangul + self.cyrillic

    @property
    def total(self) -> int:
        return (
            self.latin + self.cjk + self.hiragana + self.katakana + self.hangul +
            self.cyrillic + self.digit + self.whitespace + self.punctuation + self.other
        )
