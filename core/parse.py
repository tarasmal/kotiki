from __future__ import annotations
from typing import List, Optional
from .ast import Node, OPS
from .tokenize import tokenize

PREC = {"+": 1, "-": 1, "*": 2, "/": 2}
ASSOC = {"+": "L", "-": "L", "*": "L", "/": "L"}
#L2
def to_rpn(tokens: List[str]) -> List[str]:
    out: List[str] = []
    stack: List[str] = []
    prev: Optional[str] = None

    for tok in tokens:
        if tok not in OPS and tok not in {"(", ")"}:
            out.append(tok)
        elif tok in OPS:
            if tok == "-" and (prev is None or prev in OPS or prev == "("):
                out.append("0")
            while stack and stack[-1] in OPS:
                top = stack[-1]
                if (PREC[top] > PREC[tok]) or (PREC[top] == PREC[tok] and ASSOC[tok] == "L"):
                    out.append(stack.pop())
                else:
                    break
            stack.append(tok)
        elif tok == "(":
            stack.append(tok)
        else:
            while stack and stack[-1] != "(":
                out.append(stack.pop())
            if not stack:
                raise ValueError("Mismatched parentheses")
            stack.pop()
        prev = tok

    while stack:
        if stack[-1] in {"(", ")"}:
            raise ValueError("Mismatched parentheses")
        out.append(stack.pop())
    return out

def rpn_to_ast(rpn: List[str]) -> Node:
    st: List[Node] = []
    for tok in rpn:
        if tok in OPS:
            if len(st) < 2:
                raise ValueError("Invalid expression")
            b = st.pop()
            a = st.pop()
            st.append(Node(tok, a, b))
        else:
            st.append(Node(tok))
    if len(st) != 1:
        raise ValueError("Invalid expression")
    return st[0]

def parse_expression(expr: str) -> Node:
    return rpn_to_ast(to_rpn(tokenize(expr)))
