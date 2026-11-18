"""数据库连接与初始化。"""
from __future__ import annotations

import os
import sqlite3
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent      # backend/
PROJECT_DIR = BASE_DIR.parent                          # zujuan/

# 部署时用 ZUJUAN_DATA_DIR 指向持久盘（如 Render 的 /var/data）；
# 不设则用项目内的 data/，本地开发行为不变。
DATA_DIR = Path(os.environ.get("ZUJUAN_DATA_DIR") or (PROJECT_DIR / "data"))
DB_PATH = Path(os.environ.get("ZUJUAN_DB") or (DATA_DIR / "zujuan.db"))
SCHEMA_PATH = Path(__file__).with_name("schema.sql")


def connect() -> sqlite3.Connection:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA journal_mode = WAL")
    return conn


def init_schema(conn: sqlite3.Connection) -> None:
    conn.executescript(SCHEMA_PATH.read_text(encoding="utf-8"))
    conn.commit()


def get_db():
    """FastAPI 依赖：每个请求一个连接。"""
    conn = connect()
    try:
        yield conn
    finally:
        conn.close()
