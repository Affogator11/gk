# -*- coding: utf-8 -*-
from __future__ import annotations

from pydantic import BaseModel, Field


class AssembleRequest(BaseModel):
    blueprint_id: int
    title: str | None = None
    target_difficulty: float | None = Field(default=None, ge=0.2, le=0.9)
    restarts: int = Field(default=6, ge=1, le=20)
    seed: int | None = None


class SwapRequest(BaseModel):
    question_id: int
