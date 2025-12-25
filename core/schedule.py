from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, List, Optional, Set, Tuple, Union
import heapq
from core.ast import Node, is_leaf
#L5

@dataclass(frozen=True)
class Task:
    id: int
    op: str
    duration: int
    deps: Tuple[int, ...]


@dataclass(frozen=True)
class TaskRun:
    task_id: int
    op: str
    proc: int
    start: int
    finish: int


def _postorder_ops(root: Node) -> List[Node]:
    out: List[Node] = []

    def dfs(n: Node) -> None:
        if n.left:
            dfs(n.left)
        if n.right:
            dfs(n.right)
        if not is_leaf(n):
            out.append(n)

    dfs(root)
    return out


def build_tasks(root: Node, op_cost: Dict[str, int]) -> Tuple[List[Task], int]:
    nodes = _postorder_ops(root)
    node_to_id: Dict[Node, int] = {}
    for idx, n in enumerate(nodes, start=1):
        node_to_id[n] = idx

    def dep_id(child: Optional[Node]) -> Optional[int]:
        if not child or is_leaf(child):
            return None
        return node_to_id[child]

    tasks: List[Task] = []
    for n in nodes:
        deps: List[int] = []
        dl = dep_id(n.left)
        dr = dep_id(n.right)
        if dl is not None:
            deps.append(dl)
        if dr is not None:
            deps.append(dr)
        dur = op_cost.get(n.value)
        if dur is None:
            raise ValueError(f"Missing op cost for '{n.value}'")
        tasks.append(Task(node_to_id[n], n.value, int(dur), tuple(sorted(deps))))

    root_task_id = node_to_id[nodes[-1]] if nodes else 0
    return tasks, root_task_id


def sequential_time(tasks: List[Task]) -> int:
    return sum(t.duration for t in tasks)


def schedule_dataflow(
    tasks: List[Task],
    processors: int,
    memory_banks: int,
    mem_cost: int,
) -> Tuple[int, List[TaskRun]]:
    if processors <= 0:
        raise ValueError("processors must be > 0")
    if memory_banks <= 0:
        raise ValueError("memory_banks must be > 0")
    if mem_cost < 0:
        raise ValueError("mem_cost must be >= 0")

    tasks_by_id: Dict[int, Task] = {t.id: t for t in tasks}
    dependents: Dict[int, List[int]] = {t.id: [] for t in tasks}
    indeg: Dict[int, int] = {t.id: len(t.deps) for t in tasks}

    for t in tasks:
        for d in t.deps:
            dependents[d].append(t.id)

    ready: List[int] = [t.id for t in tasks if indeg[t.id] == 0]
    ready.sort()

    proc_free: List[Tuple[int, int]] = [(0, p) for p in range(processors)]
    heapq.heapify(proc_free)

    bank_free: List[int] = [0 for _ in range(memory_banks)]

    running: List[Tuple[int, int, int]] = []
    heapq.heapify(running)

    finish_time: Dict[int, int] = {}
    runs: List[TaskRun] = []
    time = 0

    def reserve_memory(start: int) -> int:
        if mem_cost == 0:
            return start
        best_i = 0
        best_t = bank_free[0]
        for i in range(1, memory_banks):
            if bank_free[i] < best_t:
                best_t = bank_free[i]
                best_i = i
        s = max(start, bank_free[best_i])
        bank_free[best_i] = s + mem_cost
        return s + mem_cost

    while len(finish_time) < len(tasks):
        started = False

        while ready and proc_free:
            t_id = ready[0]
            t = tasks_by_id[t_id]
            p_time, p = heapq.heappop(proc_free)

            deps_done = 0
            for d in t.deps:
                deps_done = max(deps_done, finish_time.get(d, 0))

            start = max(time, p_time, deps_done)
            start = reserve_memory(start)
            finish = start + t.duration

            runs.append(TaskRun(t_id, t.op, p, start, finish))
            heapq.heappush(running, (finish, t_id, p))
            ready.pop(0)
            started = True

        if running:
            finish, t_id, p = heapq.heappop(running)
            time = max(time, finish)
            finish_time[t_id] = finish
            heapq.heappush(proc_free, (time, p))

            for nxt in dependents[t_id]:
                indeg[nxt] -= 1
                if indeg[nxt] == 0:
                    ready.append(nxt)
            ready.sort()
        else:
            if not started and proc_free:
                time = max(time, proc_free[0][0])
            else:
                time += 1

    makespan = max(r.finish for r in runs) if runs else 0
    return makespan, sorted(runs, key=lambda x: (x.start, x.proc, x.task_id))
