# -*- coding: utf-8 -*-
"""启动脚本：python run.py  （默认 http://127.0.0.1:8123）"""
from __future__ import annotations

import os
import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BACKEND_DIR / "vendor"))
sys.path.insert(0, str(BACKEND_DIR))

import uvicorn  # noqa: E402

if __name__ == "__main__":
    host = os.environ.get("HOST", "127.0.0.1")
    port = int(os.environ.get("PORT", "8123"))
    print(f"服务地址：http://{host}:{port}")
    uvicorn.run("app.main:app", host=host, port=port, reload=False, log_level="info")
