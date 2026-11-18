# -*- coding: utf-8 -*-
"""组卷引擎。

把组卷看成「带约束的多目标选配」问题：
1. 细目表展开成有序槽位（每个槽位有题型、分值、目标难度）；
2. 贪心构造可行解，保证每个槽位都有题；
3. 局部搜索（随机交换 + 爬山）优化整体目标函数；
4. 多次随机重启取最优。

目标函数 = 难度贴合度 + 知识点覆盖度 + 答案分布均衡 - 重复惩罚。
"""
from __future__ import annotations

import math
import random

RAMP = 0.16      # 难度梯度：首题比目标略易，末题略难
DIFF_TOL = 0.35  # 难度允许区间


def expand_slots(bp: dict, ramp: float = RAMP) -> list[dict]:
    """把细目表展开成有序槽位列表。"""
    slots: list[dict] = []
    pos = 0
    for sec in bp["sections"]:
        scores = sec.get("scores") or [sec.get("score")] * sec["count"]
        for i, sc in enumerate(scores):
            pos += 1
            slots.append({
                "position": pos,
                "section": sec["key"],
                "section_label": sec["label"],
                "qtype": sec["qtype"],
                "index_in_section": i,
                "score": float(sc),
            })
    n = len(slots)
    for s in slots:
        r = (s["position"] - 1) / max(n - 1, 1)
        s["target"] = round(min(0.92, max(0.18, bp["target_difficulty"] + ramp - 2 * ramp * r)), 3)
    return slots


def difficulty_ceiling(bp: dict, pools: dict[str, list[dict]]) -> float:
    """当前题库能支撑的最高整卷难度（各题型取难度最高的一组题）。"""
    total, weighted = 0.0, 0.0
    for sec in bp["sections"]:
        scores = sec.get("scores") or [sec.get("score")] * sec["count"]
        pool = sorted(pools.get(sec["qtype"], []), key=lambda q: -q["difficulty"])[: sec["count"]]
        for q, sc in zip(pool, scores):
            weighted += q["difficulty"] * float(sc)
            total += float(sc)
    return round(weighted / total, 3) if total else 0.0


def _coverage(selection: list[dict], slots: list[dict], cells: dict[str, float]) -> float:
    achieved: dict[str, float] = {c: 0.0 for c in cells}
    for q, s in zip(selection, slots):
        code = q["knowledge_code"]
        if code in achieved:
            achieved[code] += s["score"]
        else:
            parent = code.split(".")[0]
            if parent in achieved:
                achieved[parent] += s["score"]
    ratios = [min(achieved[c], t) / t for c, t in cells.items() if t > 0]
    return sum(ratios) / len(ratios) if ratios else 0.0


def _answer_balance(selection: list[dict]) -> float:
    counts: dict[str, int] = {}
    for q in selection:
        if q["qtype"] == "single":
            counts[q["answer"]] = counts.get(q["answer"], 0) + 1
    if not counts:
        return 1.0
    total = sum(counts.values())
    entropy = 0.0
    for c in counts.values():
        p = c / total
        entropy -= p * math.log(p)
    return min(1.0, entropy / math.log(4))


def evaluate(selection: list[dict], slots: list[dict], cells: dict[str, float]) -> float:
    dev = sum(abs(q["difficulty"] - s["target"]) for q, s in zip(selection, slots)) / len(slots)
    cover = _coverage(selection, slots, cells)
    balance = _answer_balance(selection)
    seen: dict[str, int] = {}
    for q in selection:
        seen[q["knowledge_code"]] = seen.get(q["knowledge_code"], 0) + 1
    dup = sum((n - 1) * 0.05 for n in seen.values() if n > 1)
    return 1.6 * (1 - min(1.0, dev / DIFF_TOL)) + 1.0 * cover + 0.25 * balance - dup


def _greedy(pools: dict[str, list[dict]], slots: list[dict],
            cells: dict[str, float], rng: random.Random) -> list[dict] | None:
    used: set[int] = set()
    selection: list[dict] = []
    deficit = dict(cells)
    answer_count: dict[str, int] = {}
    kp_count: dict[str, int] = {}

    for s in slots:
        pool = pools.get(s["qtype"], [])
        best, best_score = None, -1e9
        for q in pool:
            if q["id"] in used:
                continue
            d_fit = max(0.0, 1 - abs(q["difficulty"] - s["target"]) / DIFF_TOL)
            need = 1.0 if deficit.get(q["knowledge_code"], 0) > 0 else 0.15
            dup_pen = 0.4 * kp_count.get(q["knowledge_code"], 0)
            novelty = 1.0 / (1 + 0.12 * q["usage_count"])
            ans_pen = 0.18 * answer_count.get(q["answer"], 0) if q["qtype"] == "single" else 0
            sc = 0.44 * d_fit + 0.34 * need + 0.10 * novelty - dup_pen - ans_pen
            sc += rng.uniform(0, 0.05)
            if sc > best_score:
                best, best_score = q, sc
        if best is None:
            return None
        used.add(best["id"])
        selection.append(best)
        deficit[best["knowledge_code"]] = max(0.0, deficit.get(best["knowledge_code"], 0) - s["score"])
        answer_count[best["answer"]] = answer_count.get(best["answer"], 0) + 1
        kp_count[best["knowledge_code"]] = kp_count.get(best["knowledge_code"], 0) + 1
    return selection


def _improve(selection: list[dict], slots: list[dict], pools: dict[str, list[dict]],
             cells: dict[str, float], rng: random.Random, rounds: int = 1500) -> list[dict]:
    sel = list(selection)
    best_fit = evaluate(sel, slots, cells)
    for _ in range(rounds):
        i = rng.randrange(len(sel))
        pool = pools.get(slots[i]["qtype"], [])
        if len(pool) < 2:
            continue
        cand = pool[rng.randrange(len(pool))]
        if any(q["id"] == cand["id"] for q in sel):
            continue
        old = sel[i]
        sel[i] = cand
        fit = evaluate(sel, slots, cells)
        if fit > best_fit:
            best_fit = fit
        else:
            sel[i] = old
    return sel


def assemble(bp: dict, pools: dict[str, list[dict]], *, restarts: int = 6,
             seed: int | None = None, ramp: float = RAMP) -> dict:
    """执行组卷。返回 {feasible, items, slots, fitness}。"""
    slots = expand_slots(bp, ramp)
    cells = {c["knowledge_code"]: float(c["score"]) for c in bp["cells"]}
    rng = random.Random(seed if seed is not None else 20261118)

    best_sel, best_fit = None, -1e9
    for _ in range(restarts):
        sel = _greedy(pools, slots, cells, rng)
        if sel is None:
            continue
        sel = _improve(sel, slots, pools, cells, rng)
        fit = evaluate(sel, slots, cells)
        if fit > best_fit:
            best_sel, best_fit = sel, fit

    if best_sel is None:
        return {"feasible": False, "items": [], "slots": slots, "fitness": 0.0}

    items = []
    for q, s in zip(best_sel, slots):
        items.append({
            "question_id": q["id"],
            "section": s["section"],
            "position": s["position"],
            "score": s["score"],
            "question": q,
        })
    return {"feasible": True, "items": items, "slots": slots, "fitness": round(best_fit, 4)}


def alternatives(pool: list[dict], chosen_ids: set[int], slot: dict, current: dict | None,
                 k: int = 5) -> list[dict]:
    """为「换一题」挑选同题型、难度接近、未使用的候选。"""
    cands = [q for q in pool
             if q["id"] not in chosen_ids and (current is None or q["id"] != current["id"])]
    cands.sort(key=lambda q: (abs(q["difficulty"] - slot["target"]), q["usage_count"]))
    return cands[:k]
