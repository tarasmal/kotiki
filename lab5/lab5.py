from __future__ import annotations
from pathlib import Path
from typing import Dict, List
from core.parse import parse_expression
from core.parallel_form import build_parallel_form
from core.equivalence import to_infix
from core.schedule import TaskRun, build_tasks, schedule_dataflow, sequential_time
from plot_lab5 import plot_schedule_to_file


OUT_DIR = Path(__file__).parent / "out"


def print_table(runs: List[TaskRun]) -> None:
    print("t_start | t_end | proc | task | op")
    print("------:|-----:|:-----|:-----|:--")
    for r in sorted(runs, key=lambda x: (x.start, x.finish, x.proc, x.task_id)):
        print(f"{r.start:>6} | {r.finish:>5} | P{r.proc:>3} | t{r.task_id:>4} | {r.op}")


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
    pf = build_parallel_form(ast)

    tasks, root_id = build_tasks(pf, op_cost)
    t1 = sequential_time(tasks)
    tp, runs = schedule_dataflow(tasks, processors=P, memory_banks=memory_banks, mem_cost=mem_cost)

    s = (t1 / tp) if tp > 0 else 0.0
    e = (s / P) if P > 0 else 0.0

    print("LR5")
    print(f"System: {system}")
    print(f"Processors (P): {P}")
    print(f"Memory banks: {memory_banks}")
    print(f"Operation costs: {op_cost}")
    print(f"Memory access cost: {mem_cost}")
    print()
    print(f"Input: {expr}")
    print(f"Parallel form: {to_infix(pf)}")
    print(f"Root task: t{root_id}")
    print(f"Tasks count: {len(tasks)}")
    print()
    print(f"T1 (sequential): {t1}")
    print(f"Tp (parallel):   {tp}")
    print(f"S = T1/Tp:       {s:.4f}")
    print(f"E = S/P:         {e:.4f}")
    print()
    print_table(runs)
    print()

    out_png = OUT_DIR / "lab5_schedule.png"
    plot_schedule_to_file(
        runs=runs,
        processors=P,
        out_path=out_png,
        title="Lab 5 — Dataflow schedule",
        t1=t1,
        tp=tp,
        s=s,
        e=e,
    )
    print(f"[OK] Schedule saved to: {out_png}")

if __name__ == "__main__":
    main()
