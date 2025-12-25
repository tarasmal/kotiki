from __future__ import annotations
from collections import defaultdict
from pathlib import Path
from typing import DefaultDict, List, Tuple
import matplotlib.pyplot as plt
from core.schedule import TaskRun


def plot_schedule_to_file(
    runs: List[TaskRun],
    processors: int,
    out_path: Path,
    title: str,
    t1: int,
    tp: int,
    s: float,
    e: float,
) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)

    rows: DefaultDict[str, List[Tuple[int, int, str]]] = defaultdict(list)

    for r in runs:
        label = f"t{r.task_id}:{r.op}"
        rows[f"P{r.proc}"].append((r.start, r.finish, label))

    order = [f"P{i}" for i in range(processors)]
    fig, ax = plt.subplots(figsize=(12, max(3, 0.7 * len(order) + 1)))

    y_pos = {name: i for i, name in enumerate(order)}
    h = 0.35

    for name in order:
        for (start, end, label) in sorted(rows.get(name, []), key=lambda x: (x[0], x[1])):
            ax.barh(y=y_pos[name], width=end - start, left=start, height=h)
            ax.text(start + (end - start) / 2, y_pos[name], label, ha="center", va="center", fontsize=8)

    ax.set_yticks([y_pos[n] for n in order])
    ax.set_yticklabels(order)
    ax.set_xlabel("Time")
    ax.set_title(f"{title}\nT1={t1}, Tp={tp}, S={s:.4f}, E={e:.4f}")
    ax.grid(True, axis="x", linestyle="--", linewidth=0.5)

    plt.tight_layout()
    plt.savefig(out_path, dpi=200)
    plt.close(fig)
