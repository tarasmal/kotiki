from __future__ import annotations
from typing import List
#L2
def tokenize(expr: str) -> List[str]:
    s = expr.replace(" ", "")
    tokens: List[str] = []
    i = 0
    while i < len(s):
        ch = s[i]
        if ch in "+-*/()":
            tokens.append(ch)
            i += 1
            continue
        if ch.isalpha() or ch == "_":
            j = i + 1
            while j < len(s) and (s[j].isalnum() or s[j] == "_"):
                j += 1
            tokens.append(s[i:j])
            i = j
            continue
        if ch.isdigit() or ch == ".":
            j = i + 1
            dot = 1 if ch == "." else 0
            while j < len(s) and (s[j].isdigit() or s[j] == "."):
                if s[j] == ".":
                    dot += 1
                j += 1
            if dot > 1:
                raise ValueError(f"Invalid number token near: {s[i:j]}")
            tokens.append(s[i:j])
            i = j
            continue
        raise ValueError(f"Unexpected char: {ch}")
    return tokens
