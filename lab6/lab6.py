from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, Iterable, List, Optional, Set, Tuple
from core.ast import Node, is_leaf
from core.parse import parse_expression
from core.parallel_form import build_parallel_form
from core.equivalence import assoc_generate, dist_generate, to_infix
from core.schedule import build_tasks, schedule_dataflow, sequential_time


@dataclass(frozen=True)
class EvalRow:
    idx: int
    expr: str
    tp: int
    t1: int
    s: float
    e: float
    ops: int


def clone(n: Node) -> Node:
    if is_leaf(n):
        return Node(n.value)
    return Node(n.value, clone(n.left) if n.left else None, clone(n.right) if n.right else None)


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


def all_assoc_trees(op: str, operands: List[Node], limit: int) -> List[Node]:
    if len(operands) == 1:
        return [clone(operands[0])]
    res: List[Node] = []
    for i in range(1, len(operands)):
        left_ops = operands[:i]
        right_ops = operands[i:]
        left_trees = all_assoc_trees(op, left_ops, limit)
        right_trees = all_assoc_trees(op, right_ops, limit)
        for lt in left_trees:
            for rt in right_trees:
                res.append(Node(op, lt, rt))
                if len(res) >= limit:
                    return res
    return res


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


def neighbors_once(root: Node, assoc_limit: int, dist_limit: int) -> List[Node]:
    out: List[Node] = []
    for node in iter_nodes(root):
        if node.value in {"+", "*"}:
            ops = collect_chain_assoc(node, node.value)
            if len(ops) >= 3:
                variants = all_assoc_trees(node.value, ops, assoc_limit + 1)
                for v in variants:
                    expr = to_infix(v)
                    if expr != to_infix(node):
                        out.append(replace_subtree(root, node, v))
                        if len(out) >= assoc_limit:
                            break
        if len(out) >= assoc_limit:
            break

    if dist_limit > 0:
        for node in iter_nodes(root):
            for repl in dist_rewrites_at_node(node):
                out.append(replace_subtree(root, node, repl))
                if len(out) >= assoc_limit + dist_limit:
                    return out
    return out


def generate_forms_for_lab6(
    base_pf: Node,
    lr3_max: int,
    lr4_max: int,
    lr4_steps: int,
) -> List[Node]:
    s: Dict[str, Node] = {}

    base_key = to_infix(base_pf)
    s[base_key] = base_pf

    for n in assoc_generate(base_pf, max_results=lr3_max):
        s.setdefault(to_infix(n), n)

    for n in dist_generate(base_pf, max_results=lr4_max, max_steps=lr4_steps):
        s.setdefault(to_infix(n), n)

    return list(s.values())


def eval_form(
    pf: Node,
    p: int,
    memory_banks: int,
    mem_cost: int,
    op_cost: Dict[str, int],
) -> Tuple[int, int, float, float, int]:
    tasks, _ = build_tasks(pf, op_cost)
    t1 = sequential_time(tasks)
    tp, _runs = schedule_dataflow(tasks, processors=p, memory_banks=memory_banks, mem_cost=mem_cost)
    s = (t1 / tp) if tp > 0 else 0.0
    e = (s / p) if p > 0 else 0.0
    return tp, t1, s, e, len(tasks)


def print_results(rows: List[EvalRow], title: str) -> None:
    print(title)
    print("idx | Tp | T1 | S | E | ops | form")
    print("---:|---:|---:|---:|---:|---:|:-----")
    for r in rows:
        print(f"{r.idx:>3} | {r.tp:>3} | {r.t1:>3} | {r.s:>6.3f} | {r.e:>6.3f} | {r.ops:>3} | {r.expr}")


def pick_optimal(rows: List[EvalRow]) -> EvalRow:
    best = rows[0]
    for r in rows[1:]:
        if r.tp < best.tp:
            best = r
        elif r.tp == best.tp:
            if r.e > best.e:
                best = r
            elif r.e == best.e and r.ops < best.ops:
                best = r
    return best


def directed_search(
    start: Node,
    p: int,
    memory_banks: int,
    mem_cost: int,
    op_cost: Dict[str, int],
    beam_width: int,
    depth: int,
    neighbors_assoc: int,
    neighbors_dist: int,
) -> List[EvalRow]:
    seen: Set[str] = set()
    frontier: List[Tuple[Node, int]] = [(start, 0)]
    best_rows: List[EvalRow] = []
    idx = 0

    def score(tp: int, e: float, ops: int) -> Tuple[int, float, int]:
        return (tp, -e, ops)

    for _ in range(depth):
        candidates: List[Tuple[Tuple[int, float, int], Node]] = []
        for node, _d in frontier:
            k = to_infix(node)
            if k in seen:
                continue
            seen.add(k)

            tp, t1, s, e, ops = eval_form(node, p, memory_banks, mem_cost, op_cost)
            idx += 1
            best_rows.append(EvalRow(idx, k, tp, t1, s, e, ops))

            for nb in neighbors_once(node, assoc_limit=neighbors_assoc, dist_limit=neighbors_dist):
                tp2, t12, s2, e2, ops2 = eval_form(nb, p, memory_banks, mem_cost, op_cost)
                candidates.append((score(tp2, e2, ops2), nb))

        candidates.sort(key=lambda x: x[0])
        new_frontier: List[Tuple[Node, int]] = []
        for _, n in candidates[:beam_width]:
            new_frontier.append((n, 0))
        frontier = new_frontier
        if not frontier:
            break

    best_rows.sort(key=lambda r: (r.tp, -r.e, r.ops))
    return best_rows


def main() -> None:
    expr = "(A+B)*(C+D+E)+F*(G+H)"

    system = "Dataflow"
    P = 2
    memory_banks = 1

    op_cost: Dict[str, int] = {
        "+": 1,
        "-": 1,
        "*": 2,
        "/": 2,
    }

    mem_cost = 1

    ast = parse_expression(expr)
    base_pf = build_parallel_form(ast)

    lr3_max = 60
    lr4_max = 60
    lr4_steps = 4

    forms = generate_forms_for_lab6(base_pf, lr3_max=lr3_max, lr4_max=lr4_max, lr4_steps=lr4_steps)

    rows: List[EvalRow] = []
    for i, pf in enumerate(forms, start=1):
        k = to_infix(pf)
        tp, t1, s, e, ops = eval_form(pf, P, memory_banks, mem_cost, op_cost)
        rows.append(EvalRow(i, k, tp, t1, s, e, ops))

    rows.sort(key=lambda r: (r.tp, -r.e, r.ops))

    print("LR6 (RGR)")
    print(f"System: {system}")
    print(f"Processors (P): {P}")
    print(f"Memory banks: {memory_banks}")
    print(f"Operation costs: {op_cost}")
    print(f"Memory access cost: {mem_cost}")
    print()
    print(f"Input: {expr}")
    print(f"Base PF: {to_infix(base_pf)}")
    print()
    print_results(rows, "Table (all equivalent PF graphs)")
    print()

    best = pick_optimal(rows)
    print("Optimal form:")
    print(f"idx={best.idx}, Tp={best.tp}, T1={best.t1}, S={best.s:.4f}, E={best.e:.4f}, ops={best.ops}")
    print(best.expr)
    print()

    beam_width = 8
    depth = 6
    neighbors_assoc = 6
    neighbors_dist = 6

    ds_rows = directed_search(
        start=base_pf,
        p=P,
        memory_banks=memory_banks,
        mem_cost=mem_cost,
        op_cost=op_cost,
        beam_width=beam_width,
        depth=depth,
        neighbors_assoc=neighbors_assoc,
        neighbors_dist=neighbors_dist,
    )

    top_k = 15
    print_results(ds_rows[:top_k], f"Directed search (top {top_k})")


if __name__ == "__main__":
    main()
