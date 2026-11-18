# -*- coding: utf-8 -*-
from fastapi import APIRouter, Depends, HTTPException, Response
from fastapi.responses import StreamingResponse

from ..db import get_db
from .. import repository as repo
from ..schemas import AssembleRequest, SwapRequest
from ..services.assemble import assemble, difficulty_ceiling
from ..services.report import build_report
from ..services.export import build_docx

router = APIRouter(tags=["papers"])

ALL_TYPES = ["single", "multi", "blank", "solve"]


def _pools(conn) -> dict:
    return {t: repo.candidate_pool(conn, t) for t in ALL_TYPES}


def _report_for(conn, paper: dict, pools: dict | None = None) -> dict:
    bp = (paper.get("constraints") or {}).get("blueprint")
    if not bp:
        raise HTTPException(500, "试卷缺少细目表快照")
    names = repo.knowledge_names(conn)
    pools = pools or _pools(conn)
    return build_report(paper["items"], bp, names, ceiling=difficulty_ceiling(bp, pools))


@router.post("/papers/assemble")
def create_paper(req: AssembleRequest, conn=Depends(get_db)):
    bp = repo.get_blueprint(conn, req.blueprint_id)
    if not bp:
        raise HTTPException(404, "细目表不存在")

    if req.target_difficulty is not None:
        bp = {**bp, "target_difficulty": req.target_difficulty}

    pools = _pools(conn)
    res = assemble(bp, pools, restarts=req.restarts, seed=req.seed)
    if not res["feasible"]:
        raise HTTPException(409, "题库中可用题目不足，无法完成组卷，请减少题量或补充题库")

    title = req.title or f"{bp['name']} · {len(res['items'])} 题"
    items = res["items"]
    difficulty = sum(i["question"]["difficulty"] * i["score"] for i in items) / sum(i["score"] for i in items)

    paper_id = repo.create_paper(
        conn,
        title=title,
        blueprint_id=bp["id"],
        total_score=bp["total_score"],
        duration_min=bp["duration_min"],
        target_difficulty=bp["target_difficulty"],
        difficulty=round(difficulty, 3),
        constraints={"blueprint": bp, "fitness": res["fitness"], "seed": req.seed},
        items=[{"question_id": i["question_id"], "section": i["section"],
                "position": i["position"], "score": i["score"]} for i in items],
    )
    repo.bump_usage(conn, [i["question_id"] for i in items])
    conn.commit()

    paper = repo.get_paper(conn, paper_id)
    return {"paper": paper, "report": _report_for(conn, paper, pools)}


@router.get("/papers")
def list_papers(conn=Depends(get_db)):
    return {"items": repo.list_papers(conn)}


@router.get("/papers/{pid}")
def get_paper(pid: int, conn=Depends(get_db)):
    paper = repo.get_paper(conn, pid)
    if not paper:
        raise HTTPException(404, "试卷不存在")
    return {"paper": paper, "report": _report_for(conn, paper)}


@router.delete("/papers/{pid}")
def delete_paper(pid: int, conn=Depends(get_db)):
    repo.delete_paper(conn, pid)
    return {"ok": True}


@router.post("/papers/{pid}/items/{item_id}/swap")
def swap_item(pid: int, item_id: int, req: SwapRequest, conn=Depends(get_db)):
    paper = repo.get_paper(conn, pid)
    if not paper:
        raise HTTPException(404, "试卷不存在")
    item = next((i for i in paper["items"] if i["item_id"] == item_id), None)
    if not item:
        raise HTTPException(404, "题目位置不存在")

    q = repo.get_question(conn, req.question_id)
    if not q:
        raise HTTPException(404, "候选题不存在")
    if q["qtype"] != item["qtype"]:
        raise HTTPException(400, "候选题题型与原题不一致")
    if any(i["id"] == q["id"] for i in paper["items"]):
        raise HTTPException(400, "该题已在卷中")

    repo.update_item_question(conn, pid, item_id, q["id"])
    paper = repo.get_paper(conn, pid)
    return {"paper": paper, "report": _report_for(conn, paper)}


@router.get("/papers/{pid}/alternatives")
def alternatives(pid: int, item_id: int, conn=Depends(get_db)):
    paper = repo.get_paper(conn, pid)
    if not paper:
        raise HTTPException(404, "试卷不存在")
    item = next((i for i in paper["items"] if i["item_id"] == item_id), None)
    if not item:
        raise HTTPException(404, "题目位置不存在")

    bp = (paper.get("constraints") or {}).get("blueprint") or {}
    from ..services.assemble import expand_slots
    slots = {s["position"]: s for s in expand_slots(bp)} if bp else {}
    slot = slots.get(item["position"], {"target": item["difficulty"]})

    chosen = {i["id"] for i in paper["items"]}
    pool = repo.candidate_pool(conn, item["qtype"])
    cands = []
    for q in sorted(pool, key=lambda x: abs(x["difficulty"] - slot.get("target", item["difficulty"]))):
        if q["id"] in chosen:
            continue
        cands.append({k: q[k] for k in ("id", "stem", "difficulty", "knowledge_code", "answer")})
        if len(cands) >= 5:
            break
    return {"items": cands}


@router.get("/papers/{pid}/export.docx")
def export_docx(pid: int, conn=Depends(get_db)):
    paper = repo.get_paper(conn, pid)
    if not paper:
        raise HTTPException(404, "试卷不存在")
    report = _report_for(conn, paper)
    data = build_docx(paper, report)
    filename = f"paper-{pid}.docx"
    return StreamingResponse(
        iter([data]),
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/stats")
def stats(conn=Depends(get_db)):
    q = conn.execute("SELECT COUNT(*) c FROM questions").fetchone()["c"]
    p = conn.execute("SELECT COUNT(*) c FROM papers").fetchone()["c"]
    b = conn.execute("SELECT COUNT(*) c FROM blueprints").fetchone()["c"]
    return {"questions": q, "papers": p, "blueprints": b}
