# -*- coding: utf-8 -*-
from fastapi import APIRouter, Depends, HTTPException

from ..db import get_db
from .. import repository as repo

router = APIRouter(tags=["blueprints"])


@router.get("/blueprints")
def list_blueprints(conn=Depends(get_db)):
    names = repo.knowledge_names(conn)
    out = []
    for b in repo.list_blueprints(conn):
        b["cells"] = [{**c, "knowledge_name": names.get(c["knowledge_code"], c["knowledge_code"])}
                      for c in b["cells"]]
        out.append(b)
    return {"items": out}


@router.get("/blueprints/{bid}")
def get_blueprint(bid: int, conn=Depends(get_db)):
    b = repo.get_blueprint(conn, bid)
    if not b:
        raise HTTPException(404, "细目表不存在")
    names = repo.knowledge_names(conn)
    b["cells"] = [{**c, "knowledge_name": names.get(c["knowledge_code"], c["knowledge_code"])}
                  for c in b["cells"]]
    return b
