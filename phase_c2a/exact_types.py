from __future__ import annotations
from fractions import Fraction
from typing import Any

class ExactInputError(TypeError):
    pass

def require_fraction(value: Any, name: str = "value") -> Fraction:
    """Accept only built-in int (not bool) and exact built-in Fraction."""
    if type(value) is bool:
        raise ExactInputError(f"{name} must not be bool")
    if type(value) is int:
        return Fraction(value)
    if type(value) is Fraction:
        return value
    raise ExactInputError(
        f"{name} must be built-in int or fractions.Fraction; got {type(value).__name__}"
    )

def parse_rational(text: str) -> Fraction:
    if type(text) is not str:
        raise ExactInputError("text must be a built-in str")
    s=text.strip()
    if not s:
        raise ValueError("empty rational text")
    # Fraction(str) interprets decimal text exactly, never via binary float.
    return Fraction(s)
