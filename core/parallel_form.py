from __future__ import annotations
from typing import List
from .ast import Node, is_leaf
#L2
def collect_chain(n: Node, op: str) -> List[Node]:
    items: List[Node] = []
    def dfs(x: Node) -> None:
        if x.value == op and x.left and x.right:
            dfs(x.left)
            dfs(x.right)
        else:
            items.append(x)
    dfs(n)
    return items

def build_balanced(op: str, operands: List[Node]) -> Node:
    nodes = operands[:]
    if not nodes:
        raise ValueError("No operands")
    while len(nodes) > 1:
        nxt: List[Node] = []
        i = 0
        while i < len(nodes):
            if i + 1 < len(nodes):
                nxt.append(Node(op, nodes[i], nodes[i + 1]))
                i += 2
            else:
                nxt.append(nodes[i])
                i += 1
        nodes = nxt
    return nodes[0]

def flatten_plus_mul(n: Node) -> Node:
    if is_leaf(n):
        return n
    left = flatten_plus_mul(n.left) if n.left else None
    right = flatten_plus_mul(n.right) if n.right else None
    cur = Node(n.value, left, right)
    if cur.value in {"+", "*"}:
        ops = [flatten_plus_mul(x) for x in collect_chain(cur, cur.value)]
        return build_balanced(cur.value, ops)
    return cur

def rewrite_div_chain(n: Node) -> Node:
    if is_leaf(n):
        return n
    left = rewrite_div_chain(n.left) if n.left else None
    right = rewrite_div_chain(n.right) if n.right else None
    cur = Node(n.value, left, right)
    if cur.value != "/":
        return cur

    denoms: List[Node] = []
    def peel(x: Node) -> Node:
        if x.value == "/" and x.left and x.right:
            denoms.append(x.right)
            return peel(x.left)
        return x

    num = peel(cur)
    denoms = [rewrite_div_chain(d) for d in denoms]

    if len(denoms) == 0:
        return num
    if len(denoms) == 1:
        return Node("/", num, denoms[0])

    denom_mul = build_balanced("*", denoms)
    return Node("/", num, denom_mul)

def rewrite_sub_chain(n: Node) -> Node:
    if is_leaf(n):
        return n
    left = rewrite_sub_chain(n.left) if n.left else None
    right = rewrite_sub_chain(n.right) if n.right else None
    cur = Node(n.value, left, right)
    if cur.value != "-":
        return cur

    subs: List[Node] = []
    def peel(x: Node) -> Node:
        if x.value == "-" and x.left and x.right:
            subs.append(x.right)
            return peel(x.left)
        return x

    a = peel(cur)
    subs = [rewrite_sub_chain(x) for x in subs]

    if len(subs) == 0:
        return a
    if len(subs) == 1:
        return Node("-", a, subs[0])

    sum_node = build_balanced("+", subs)
    return Node("-", a, sum_node)

def build_parallel_form(ast: Node) -> Node:
    t1 = rewrite_div_chain(ast)
    t2 = rewrite_sub_chain(t1)
    t3 = flatten_plus_mul(t2)
    return t3
