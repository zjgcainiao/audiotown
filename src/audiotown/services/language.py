import unicodedata

class TextLangService:
    # Han
    R_CJK = [(0x4E00, 0x9FFF), (0x3400, 0x4DBF)]  
    # japanese             
    R_HIRAGANA = [(0x3040, 0x309F)]
    R_KATAKANA = [(0x30A0, 0x30FF), (0x31F0, 0x31FF)]
    # Hangul (한글) is the native, scientific alphabet used to write the Korean language
    R_HANGUL = [(0xAC00, 0xD7AF), (0x1100, 0x11FF)]
    # cryilic - denoting the alphabet used by many Slavic peoples
    R_CYRILLIC = [(0x0400, 0x04FF), (0x0500, 0x052F)]
    
    def normalize_text(self, text: str):
        if text is None:
            return None
        # return text.strip()
        return unicodedata.normalize("NFKC", text).strip()
    
    # def count_scripts(self, text:str):
    def _count_in_ranges(self, s: str, ranges: list[tuple[int, int]]) -> int:
        n = 0
        for ch in s:
            o = ord(ch)
            for a, b in ranges:
                if a <= o <= b:
                    n += 1
                    break
        return n

    def detect_language_hint(self, text:str):
        pass
    def score_text_quality(self,text: str):
        pass


class MojibakeRepairService:
    def generate_candidates(self):
        pass
    def score_candidates(self):
        pass
    def choose_best_repair(self):
        pass