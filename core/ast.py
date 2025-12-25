from __future__ import annotations
from dataclasses import dataclass
from typing import Optional
#L2
OPS = {"+", "-", "*", "/"}

@dataclass
class Node:
    value: str
    left: Optional["Node"] = None
    right: Optional["Node"] = None
    __hash__ = object.__hash__

def is_leaf(n: Node) -> bool:
    return n.left is None and n.right is None
