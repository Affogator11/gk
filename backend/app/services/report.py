# -*- coding: utf-8 -*-
"""试卷体检报告：把「这套卷难不难、覆盖全不全」变成可读的指标。"""
from __future__ import annotations

import math

from .assemble import expand_slots, _coverage, _answer_balance

PSY_LEVELS = {"understand": "理解", "apply": "掌握", "analyze": "综合运用"}
QTYPE_LABELS = {"single": "单项选择", "multi": "多项选择", "blank": "填空题", "solve": "解答题"}


def _band(d: float) -> str:
    if d >= 0.7:
        return "易"
    if d >= 0.4:
        return "中"
    return "难"


def _b_from_d(d: float) -> float:
    d = min(0.98, max(0.02, d))
    return math.log((1 - d) / d)


def _normal_pdf(x: float) -> float:
    return math.exp(-0.5 * x * x) / math.sqrt(2 * math.pi)


def predict_scores(items: list[dict], total_score: float, mu: float = 0.0, sigma: float = 1.0) -> dict:
    """基于 1PL 模型估计不同能力水平考生的期望得分。"""
    bs = [(_b_from_d(it["difficulty"]), it["score"]) for it in items]
    pts = [(-3 + 0.25 * i) for i in range(25)]

    def expect(theta: float) -> float:
        return sum(s / (1 + math.exp(-(theta - b - mu) / max(sigma, 0.05))) for b, s in bs)

    curve = [{"theta": round(t, 2), "score": round(expect(t), 1)} for t in pts]
    mean_score = expect(0.0)
    pass_line = total_score * 0.6
    pass_p = sum(
        _normal_pdf(t) * (1.0 if expect(t) >= pass_line else 0.0) for t in pts
    ) / sum(_normal_pdf(t) for t in pts)

    return {
        "expected_mean": round(mean_score, 1),
        "expected_rate": round(mean_score / total_score * 100, 1),
        "pass_probability": round(pass_p * 100, 1),
        "curve": curve,
    }


def build_report(items: list[dict], blueprint: dict, names: dict[str, str],
                 ceiling: float | None = None) -> dict:
    total_score = sum(i["score"] for i in items)
    weighted = sum(i["difficulty"] * i["score"] for i in items) / total_score if total_score else 0
    target = float(blueprint["target_difficulty"])
    duration = int(blueprint["duration_min"])

    slots = {s["position"]: s for s in expand_slots(blueprint)}
    ordered = sorted(items, key=lambda i: i["position"])
    curve = []
    for it in ordered:
        s = slots.get(it["position"], {})
        curve.append({
            "position": it["position"],
            "difficulty": round(it["difficulty"], 2),
            "target": s.get("target", target),
            "band": _band(it["difficulty"]),
        })

    cells = {c["knowledge_code"]: float(c["score"]) for c in blueprint["cells"]}
    selection = [it for it in ordered]
    cover_ratio = _coverage(selection, [slots[i["position"]] for i in ordered], cells)

    achieved: dict[str, float] = {c: 0.0 for c in cells}
    for it in ordered:
        code = it["knowledge_code"]
        if code in achieved:
            achieved[code] += it["score"]
        elif code.split(".")[0] in achieved:
            achieved[code.split(".")[0]] += it["score"]

    coverage = []
    for code, goal in cells.items():
        got = achieved.get(code, 0.0)
        coverage.append({
            "code": code,
            "name": names.get(code, code),
            "target": goal,
            "achieved": got,
            "ratio": round(min(got, goal) / goal, 2) if goal else 1.0,
        })

    sections = []
    for sec in blueprint["sections"]:
        seg = [i for i in ordered if i["section"] == sec["key"]]
        if not seg:
            continue
        seg_score = sum(i["score"] for i in seg)
        sections.append({
            "key": sec["key"],
            "label": sec["label"],
            "hint": sec.get("hint", ""),
            "count": len(seg),
            "score": seg_score,
            "difficulty": round(sum(i["difficulty"] * i["score"] for i in seg) / seg_score, 2),
        })

    cog: dict[str, float] = {}
    for it in ordered:
        cog[it["cognitive"]] = cog.get(it["cognitive"], 0) + it["score"]
    cognitive = [{"key": k, "label": PSY_LEVELS.get(k, k), "score": v,
                  "percent": round(v / total_score * 100, 1)} for k, v in cog.items()]

    answers: dict[str, int] = {}
    for it in ordered:
        if it["qtype"] == "single":
            answers[it["answer"]] = answers.get(it["answer"], 0) + 1

    est_time = sum(it.get("time_min") or 0 for it in ordered)
    balance = _answer_balance(ordered)

    diff_score = 30 * max(0.0, 1 - abs(weighted - target) / 0.12)
    cover_score = 30 * cover_ratio
    struct_score = 20 * (1.0 if abs(total_score - 150) < 0.5 or abs(total_score - 100) < 0.5 else 0.8)
    bal_score = 10 * balance
    time_score = 10 * max(0.0, 1 - abs(est_time - duration) / max(duration, 1))
    health = round(diff_score + cover_score + struct_score + bal_score + time_score)

    return {
        "total_score": total_score,
        "question_count": len(ordered),
        "difficulty": round(weighted, 3),
        "target_difficulty": target,
        "difficulty_gap": round(weighted - target, 3),
        "duration_min": duration,
        "est_time": round(est_time, 1),
        "health": min(100, health),
        "coverage_ratio": round(cover_ratio, 3),
        "curve": curve,
        "coverage": coverage,
        "sections": sections,
        "cognitive": cognitive,
        "answer_distribution": answers,
        "prediction": predict_scores(ordered, total_score),
        "difficulty_ceiling": ceiling,
        "warnings": _warnings(weighted, target, cover_ratio, est_time, duration, ordered, ceiling),
    }


def _warnings(weighted: float, target: float, cover: float, est: float, duration: int,
              items: list[dict], ceiling: float | None = None) -> list[str]:
    out = []
    if ceiling is not None and target > ceiling + 0.015:
        out.append(f"题库当前最高只能支撑难度 {ceiling:.2f}，低于目标 {target:.2f}；"
                   f"需补充难题才能达到该难度。")
    elif abs(weighted - target) > 0.06:
        out.append(f"整卷难度 {weighted:.2f} 与目标 {target:.2f} 偏差较大，建议调整目标或重新生成。")
    if cover < 0.8:
        out.append(f"知识点覆盖仅 {cover*100:.0f}%，部分考点配额未满足。")
    if est > duration * 1.1:
        out.append(f"预估用时 {est:.0f} 分钟，超出考试时长 {duration} 分钟。")
    if est < duration * 0.75:
        out.append(f"预估用时 {est:.0f} 分钟，明显少于考试时长 {duration} 分钟。")
    dup = {}
    for it in items:
        dup[it["knowledge_code"]] = dup.get(it["knowledge_code"], 0) + 1
    heavy = [k for k, v in dup.items() if v >= 3]
    if heavy:
        out.append("部分考点题目偏多：" + "、".join(heavy))
    return out
