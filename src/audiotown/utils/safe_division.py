from typing import Optional, Union
def safe_division(n1: Union[int, float], n2: Union[int, float]) -> Optional[float]:
    try:
        result = float(n1 / n2)
        return result
    except ZeroDivisionError:
        return float(0.0)
    except Exception:
        return None