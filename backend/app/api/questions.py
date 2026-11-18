# -*- coding: utf-8 -*-
from fastapi import APIRouter, Depends, HTTPException, Query

from ..db import get_db
from .. import repository as repo

router = APIRouter(tags=["questions"])


@router.get("/questions")
def list_questions(
    qtype: str | None = None,
    knowledge: str | None = None,
    difficulty_min: float | None = None,
    difficulty_max: float | None = None,
    keyword: str | None = None,
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    conn=Depends(get_db),
):
    res = repo.list_questions(
        conn, qtype=qtype, knowledge=knowledge, difficulty_min=difficulty_min,
        difficulty_max=difficulty_max, keyword=keyword, limit=size, offset=(page - 1) * size,
    )
    names = repo.knowledge_names(conn)
    for q in res["items"]:
        q["knowledge_name"] = names.get(q["knowledge_code"], q["knowledge_code"])
    return {**res, "page": page, "size": size}


@router.get("/questions/{qid}")
def get_question(qid: int, conn=Depends(get_db)):
    q = repo.get_question(conn, qid)
    if not q:
        raise HTTPException(404, "题目不存在")
    q["knowledge_name"] = repo.knowledge_names(conn).get(q["knowledge_code"], q["knowledge_code"])
    return q
