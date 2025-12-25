from __future__ import annotations
from typing import Dict, Tuple, Union
from pathlib import Path
import matplotlib.pyplot as plt
from core.ast import Node, is_leaf

PathLike = Union[str, Path]

def compute_positions(root: Node) -> Dict[Node, Tuple[float, float]]:
    widths: Dict[Node, float] = {}

    def width(n: Node) -> float:
        if is_leaf(n):
            widths[n] = 1.0
            return 1.0
        wl = width(n.left) if n.left else 0.0
        wr = width(n.right) if n.right else 0.0
        widths[n] = max(1.0, wl + wr)
        return widths[n]

    width(root)

    pos: Dict[Node, Tuple[float, float]] = {}

    def assign(n: Node, x0: float, x1: float, y: float) -> None:
        pos[n] = ((x0 + x1) / 2, y)
        if n.left and n.right:
            wl = widths[n.left]
            wr = widths[n.right]
            total = wl + wr
            split = x0 + (x1 - x0) * (wl / total)
            assign(n.left, x0, split, y - 1)
            assign(n.right, split, x1, y - 1)
        elif n.left:
            assign(n.left, x0, x1, y - 1)
        elif n.right:
            assign(n.right, x0, x1, y - 1)

    assign(root, 0.0, widths[root], 0.0)
    return pos

def draw_tree(root: Node, title: str, outpath: PathLike) -> None:
    out = Path(outpath)
    out.parent.mkdir(parents=True, exist_ok=True)

    pos = compute_positions(root)
    fig, ax = plt.subplots(figsize=(14, 8))
    ax.axis("off")

    def draw_edges(n: Node) -> None:
        x, y = pos[n]
        for child in (n.left, n.right):
            if child:
                xc, yc = pos[child]
                ax.plot([x, xc], [y, yc], linewidth=2)
                draw_edges(child)

    draw_edges(root)

    for n, (x, y) in pos.items():
        ax.scatter([x], [y], s=1600)
        ax.text(x, y, n.value, ha="center", va="center", fontsize=14, fontweight="bold")

    ax.set_title(title, fontsize=14)
    fig.tight_layout()
    fig.savefig(out, dpi=220)
    plt.close(fig)
#L2