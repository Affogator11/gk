# -*- coding: utf-8 -*-
"""FastAPI 应用入口。

启动时自动建表并在空库中灌入示例数据（ZUJUAN_AUTO_INIT=0 可关闭）。
"""
from __future__ import annotations

import os
import sys
from contextlib import asynccontextmanager
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent.parent
VENDOR = BACKEND_DIR / "vendor"
if VENDOR.exists():
    sys.path.insert(0, str(VENDOR))

from fastapi import FastAPI                      # noqa: E402
from fastapi.middleware.cors import CORSMiddleware  # noqa: E402
from fastapi.staticfiles import StaticFiles      # noqa: E402

from .db import connect, init_schema, PROJECT_DIR  # noqa: E402
from .seed import seed                            # noqa: E402
from .api import meta, knowledge, questions, blueprints, papers  # noqa: E402


def bootstrap() -> dict:
    """建表 + 空库灌示例数据，重复调用无副作用。"""
    conn = connect()
    try:
        init_schema(conn)
        return seed(conn)
    finally:
        conn.close()


@asynccontextmanager
async def lifespan(_app: FastAPI):
    if os.environ.get("ZUJUAN_AUTO_INIT", "1") != "0":
        print("[bootstrap]", bootstrap(), flush=True)
    yield


app = FastAPI(title="知卷 · 智能组卷 API", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(meta.router, prefix="/api")
app.include_router(knowledge.router, prefix="/api")
app.include_router(questions.router, prefix="/api")
app.include_router(blueprints.router, prefix="/api")
app.include_router(papers.router, prefix="/api")


@app.get("/api/health")
def health():
    return {"status": "ok"}


WEB_DIR = PROJECT_DIR / "web"
if WEB_DIR.exists():
    app.mount("/", StaticFiles(directory=str(WEB_DIR), html=True), name="web")
