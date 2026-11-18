# -*- coding: utf-8 -*-
"""启动脚本：python run.py  （默认 http://127.0.0.1:8123）"""
from __future__ import annotations

import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BACKEND_DIR / "vendor"))
sys.path.insert(0, str(BACKEND_DIR))

import uvicorn  # noqa: E402

if __name__ == "__main__":
    from app.main import bootstrap
    info = bootstrap()
    print("题库初始化：", info)
    uvicorn.run("app.main:app", host="127.0.0.1", port=8123, reload=False, log_level="info")
