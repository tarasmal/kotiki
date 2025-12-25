from __future__ import annotations
from typing import List, Set, Tuple
from core.ast import Node, is_leaf

#L_3_4
def clone(n: Node) -> Node:
    if is_leaf(n):
        return Node(n.value)
    return Node(n.value, clone(n.left) if n.left else None, clone(n.right) if n.right else None)


def to_infix(n: Node) -> str:
    if is_leaf(n):
        return n.value
    if not n.left or not n.right:
        raise ValueError("Invalid AST")
    return f"({to_infix(n.left)}{n.value}{to_infix(n.right)})"


def iter_nodes(root: Node) -> List[Node]:
    acc: List[Node] = []

    def dfs(x: Node) -> None:
        acc.append(x)
        if x.left:
            dfs(x.left)
        if x.right:
            dfs(x.right)

    dfs(root)
    return acc


def replace_subtree(root: Node, target: Node, replacement: Node) -> Node:
    if root is target:
        return replacement
    if is_leaf(root):
        return Node(root.value)
    left = replace_subtree(root.left, target, replacement) if root.left else None
    right = replace_subtree(root.right, target, replacement) if root.right else None
    return Node(root.value, left, right)


def collect_chain_assoc(n: Node, op: str) -> List[Node]:
    items: List[Node] = []

    def dfs(x: Node) -> None:
        if x.value == op and x.left and x.right:
            dfs(x.left)
            dfs(x.right)
        else:
            items.append(x)

    dfs(n)
    return items


def all_assoc_trees(op: str, operands: List[Node]) -> List[Node]:
    if len(operands) == 1:
        return [clone(operands[0])]
    res: List[Node] = []
    for i in range(1, len(operands)):
        left_ops = operands[:i]
        right_ops = operands[i:]
        left_trees = all_assoc_trees(op, left_ops)
        right_trees = all_assoc_trees(op, right_ops)
        for lt in left_trees:
            for rt in right_trees:
                res.append(Node(op, lt, rt))
    return res


def assoc_generate(root: Node, max_results: int) -> List[Node]:
    base = clone(root)
    seen: Set[str] = set()
    q: List[Node] = []
    out: List[Node] = []

    def push(x: Node) -> None:
        k = to_infix(x)
        if k in seen:
            return
        seen.add(k)
        out.append(x)
        q.append(x)

    push(base)

    while q and len(out) < max_results:
        cur = q.pop(0)
        for node in iter_nodes(cur):
            if node.value not in {"+", "*"}:
                continue
            ops = collect_chain_assoc(node, node.value)
            if len(ops) <= 2:
                continue
            variants = all_assoc_trees(node.value, ops)
            for v in variants:
                push(replace_subtree(cur, node, v))
                if len(out) >= max_results:
                    break
            if len(out) >= max_results:
                break

    return out[:max_results]


def dist_rewrites_at_node(node: Node) -> List[Node]:
    if not node.left or not node.right:
        return []

    res: List[Node] = []

    if node.value == "*":
        a = node.left
        b = node.right

        if b.value == "+" and b.left and b.right:
            left = Node("*", clone(a), clone(b.left))
            right = Node("*", clone(a), clone(b.right))
            res.append(Node("+", left, right))

        if a.value == "+" and a.left and a.right:
            left = Node("*", clone(a.left), clone(b))
            right = Node("*", clone(a.right), clone(b))
            res.append(Node("+", left, right))

    if node.value == "+":
        x = node.left
        y = node.right
        if x and y and x.value == "*" and y.value == "*" and x.left and x.right and y.left and y.right:
            if to_infix(x.left) == to_infix(y.left):
                res.append(Node("*", clone(x.left), Node("+", clone(x.right), clone(y.right))))
            if to_infix(x.right) == to_infix(y.right):
                res.append(Node("*", Node("+", clone(x.left), clone(y.left)), clone(x.right)))

    return res


def dist_generate(root: Node, max_results: int, max_steps: int) -> List[Node]:
    base = clone(root)
    seen: Set[str] = set()
    out: List[Node] = []
    frontier: List[Tuple[Node, int]] = []

    def push(x: Node, d: int) -> None:
        k = to_infix(x)
        if k in seen:
            return
        seen.add(k)
        out.append(x)
        frontier.append((x, d))

    push(base, 0)

    while frontier and len(out) < max_results:
        cur, d = frontier.pop(0)
        if d >= max_steps:
            continue

        for node in iter_nodes(cur):
            for repl in dist_rewrites_at_node(node):
                push(replace_subtree(cur, node, repl), d + 1)
                if len(out) >= max_results:
                    break
            if len(out) >= max_results:
                break

    return out[:max_results]
