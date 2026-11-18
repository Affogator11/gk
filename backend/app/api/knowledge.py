# -*- coding: utf-8 -*-
from fastapi import APIRouter, Depends

from ..db import get_db
from .. import repository as repo

router = APIRouter(tags=["knowledge"])


def _decorate(nodes, counts):
    for n in nodes:
        n["question_count"] = counts.get(n["code"], 0)
        _decorate(n["children"], counts)
    return nodes


@router.get("/knowledge")
def get_knowledge(conn=Depends(get_db)):
    rows = conn.execute(
        "SELECT knowledge_code, COUNT(*) c FROM questions GROUP BY knowledge_code"
    ).fetchall()
    counts = {r["knowledge_code"]: r["c"] for r in rows}
    return {"tree": _decorate(repo.knowledge_tree(conn), counts)}
