# -*- coding: utf-8 -*-
"""数据访问层：所有 SQL 集中在这里，服务层不直接写 SQL。"""
from __future__ import annotations

import json
import sqlite3
from typing import Any, Iterable


# ---------------------------------------------------------------- 知识点
def knowledge_rows(conn: sqlite3.Connection) -> list[dict]:
    rows = conn.execute(
        "SELECT code,name,parent_code,level,sort FROM knowledge_points ORDER BY level,sort,code"
    ).fetchall()
    return [dict(r) for r in rows]


def knowledge_tree(conn: sqlite3.Connection) -> list[dict]:
    rows = knowledge_rows(conn)
    by_code = {r["code"]: {**r, "children": []} for r in rows}
    roots = []
    for r in rows:
        node = by_code[r["code"]]
        if r["parent_code"] and r["parent_code"] in by_code:
            by_code[r["parent_code"]]["children"].append(node)
        else:
            roots.append(node)
    return roots


def subtree_codes(conn: sqlite3.Connection, code: str) -> list[str]:
    rows = knowledge_rows(conn)
    children: dict[str, list[str]] = {}
    for r in rows:
        children.setdefault(r["parent_code"], []).append(r["code"])
    out, stack = [], [code]
    while stack:
        cur = stack.pop()
        out.append(cur)
        stack.extend(children.get(cur, []))
    return out


def knowledge_names(conn: sqlite3.Connection) -> dict[str, str]:
    return {r["code"]: r["name"] for r in knowledge_rows(conn)}


# ---------------------------------------------------------------- 题目
def _row_to_question(row: sqlite3.Row) -> dict:
    q = dict(row)
    q["options"] = json.loads(q["options"]) if q["options"] else []
    q["tags"] = json.loads(q["tags"]) if q["tags"] else []
    return q


def list_questions(conn, *, qtype=None, knowledge=None, difficulty_min=None,
                   difficulty_max=None, keyword=None, limit=200, offset=0) -> dict:
    where, params = ["1=1"], []
    if qtype:
        where.append("qtype = ?")
        params.append(qtype)
    if knowledge:
        codes = subtree_codes(conn, knowledge)
        where.append("knowledge_code IN (%s)" % ",".join("?" * len(codes)))
        params.extend(codes)
    if difficulty_min is not None:
        where.append("difficulty >= ?")
        params.append(difficulty_min)
    if difficulty_max is not None:
        where.append("difficulty <= ?")
        params.append(difficulty_max)
    if keyword:
        where.append("stem LIKE ?")
        params.append(f"%{keyword}%")

    clause = " AND ".join(where)
    total = conn.execute(f"SELECT COUNT(*) FROM questions WHERE {clause}", params).fetchone()[0]
    rows = conn.execute(
        f"SELECT * FROM questions WHERE {clause} ORDER BY id LIMIT ? OFFSET ?",
        (*params, limit, offset),
    ).fetchall()
    return {"total": total, "items": [_row_to_question(r) for r in rows]}


def get_question(conn, qid: int) -> dict | None:
    row = conn.execute("SELECT * FROM questions WHERE id=?", (qid,)).fetchone()
    return _row_to_question(row) if row else None


def questions_by_ids(conn, ids: Iterable[int]) -> dict[int, dict]:
    ids = list(ids)
    if not ids:
        return {}
    rows = conn.execute(
        f"SELECT * FROM questions WHERE id IN ({','.join('?' * len(ids))})", ids
    ).fetchall()
    return {r["id"]: _row_to_question(r) for r in rows}


def candidate_pool(conn, qtype: str) -> list[dict]:
    rows = conn.execute(
        "SELECT * FROM questions WHERE qtype=? ORDER BY usage_count ASC, id", (qtype,)
    ).fetchall()
    return [_row_to_question(r) for r in rows]


def bump_usage(conn, ids: Iterable[int]) -> None:
    ids = list(ids)
    if ids:
        conn.execute(
            f"UPDATE questions SET usage_count = usage_count + 1 WHERE id IN ({','.join('?' * len(ids))})",
            ids,
        )


# ---------------------------------------------------------------- 细目表
def _row_to_blueprint(row: sqlite3.Row) -> dict:
    b = dict(row)
    b["sections"] = json.loads(b["sections"])
    b["cells"] = json.loads(b["cells"])
    return b


def list_blueprints(conn) -> list[dict]:
    rows = conn.execute("SELECT * FROM blueprints ORDER BY id").fetchall()
    return [_row_to_blueprint(r) for r in rows]


def get_blueprint(conn, bid: int) -> dict | None:
    row = conn.execute("SELECT * FROM blueprints WHERE id=?", (bid,)).fetchone()
    return _row_to_blueprint(row) if row else None


# ---------------------------------------------------------------- 试卷
def create_paper(conn, *, title, blueprint_id, total_score, duration_min,
                 target_difficulty, difficulty, constraints, items) -> int:
    cur = conn.execute(
        """INSERT INTO papers(title,subject,blueprint_id,total_score,duration_min,
               target_difficulty,difficulty,status,constraints)
           VALUES(?,?,?,?,?,?,?,'ready',?)""",
        (title, "math", blueprint_id, total_score, duration_min, target_difficulty,
         difficulty, json.dumps(constraints, ensure_ascii=False)),
    )
    paper_id = cur.lastrowid
    for it in items:
        conn.execute(
            "INSERT INTO paper_items(paper_id,question_id,section,position,score) VALUES(?,?,?,?,?)",
            (paper_id, it["question_id"], it["section"], it["position"], it["score"]),
        )
    conn.commit()
    return paper_id


def list_papers(conn) -> list[dict]:
    rows = conn.execute(
        """SELECT p.id, p.title, p.subject, p.blueprint_id, p.total_score, p.duration_min,
                  p.target_difficulty, p.difficulty, p.status, p.created_at,
                  (SELECT COUNT(*) FROM paper_items i WHERE i.paper_id=p.id) AS question_count
           FROM papers p ORDER BY p.id DESC"""
    ).fetchall()
    return [dict(r) for r in rows]


def get_paper(conn, pid: int) -> dict | None:
    row = conn.execute("SELECT * FROM papers WHERE id=?", (pid,)).fetchone()
    if not row:
        return None
    paper = dict(row)
    paper["constraints"] = json.loads(paper["constraints"]) if paper["constraints"] else {}
    items = conn.execute(
        """SELECT i.id AS item_id, i.section, i.position, i.score, q.*
           FROM paper_items i JOIN questions q ON q.id = i.question_id
           WHERE i.paper_id=? ORDER BY i.position""",
        (pid,),
    ).fetchall()
    paper["items"] = []
    for r in items:
        d = dict(r)
        d["options"] = json.loads(d["options"]) if d["options"] else []
        paper["items"].append(d)
    return paper


def update_item_question(conn, paper_id: int, item_id: int, question_id: int) -> None:
    conn.execute(
        "UPDATE paper_items SET question_id=? WHERE id=? AND paper_id=?",
        (question_id, item_id, paper_id),
    )
    conn.commit()


def delete_paper(conn, pid: int) -> None:
    conn.execute("DELETE FROM papers WHERE id=?", (pid,))
    conn.commit()
