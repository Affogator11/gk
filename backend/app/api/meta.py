# -*- coding: utf-8 -*-
from fastapi import APIRouter

router = APIRouter(tags=["meta"])

QTYPES = [
    {"key": "single", "label": "单项选择题", "abbr": "单选"},
    {"key": "multi", "label": "多项选择题", "abbr": "多选"},
    {"key": "blank", "label": "填空题", "abbr": "填空"},
    {"key": "solve", "label": "解答题", "abbr": "解答"},
]

COGNITIVE = [
    {"key": "understand", "label": "理解"},
    {"key": "apply", "label": "掌握"},
    {"key": "analyze", "label": "综合运用"},
]

BANDS = [
    {"key": "easy", "label": "易", "min": 0.7},
    {"key": "mid", "label": "中", "min": 0.4},
    {"key": "hard", "label": "难", "min": 0.0},
]


@router.get("/meta")
def get_meta():
    return {
        "app": {"name": "知卷", "subtitle": "智能组卷工作台", "version": "0.1.0"},
        "subjects": [{"key": "math", "label": "数学"}],
        "qtypes": QTYPES,
        "cognitive": COGNITIVE,
        "bands": BANDS,
    }
