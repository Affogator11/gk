# -*- coding: utf-8 -*-
import sys, sqlite3, importlib
sys.path.insert(0, r"D:\文件\有趣的游戏\zujuan\\backend")
sys.path.insert(0, r"D:\文件\有趣的游戏\zujuan\\backend\\vendor")
from app import repository as repo
from app.services import assemble as A

conn = sqlite3.connect(r"D:\文件\有趣的游戏\zujuan\\data\\zujuan.db")
conn.row_factory = sqlite3.Row
bp = repo.get_blueprint(conn, 1)
pools = {t: repo.candidate_pool(conn, t) for t in ("single", "multi", "blank", "solve")}
cells = {c["knowledge_code"]: float(c["score"]) for c in bp["cells"]}

def run(tol, targets=(0.5, 0.55, 0.6)):
    A.DIFF_TOL = tol
    out = []
    for t in targets:
        b = dict(bp); b["target_difficulty"] = t
        res = A.assemble(b, pools, restarts=8, seed=7)
        items, slots = res["items"], res["slots"]
        tot = sum(i["score"] for i in items)
        d = sum(i["question"]["difficulty"] * i["score"] for i in items) / tot
        cov = A._coverage([i["question"] for i in items], slots, cells)
        out.append((t, round(d, 3), round(cov, 3)))
    return out

for tol in (0.35, 0.25, 0.2, 0.15):
    print("tol", tol, run(tol))

A.DIFF_TOL = 0.35
best = []
for sec in bp["sections"]:
    sc = sec.get("score") or sec.get("scores")
    per = sc if isinstance(sc, list) else [sc] * sec["count"]
    pool = sorted(pools[sec["qtype"]], key=lambda q: -q["difficulty"])[: sec["count"]]
    best += [(q, p) for q, p in zip(pool, per)]
tot = sum(s for _, s in best)
print("theoretical max difficulty =", round(sum(q["difficulty"] * s for q, s in best) / tot, 3))
