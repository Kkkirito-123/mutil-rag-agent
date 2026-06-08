"""Evidence Store contracts."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from app.incidents.models import EvidenceSource


class EvidenceCreate(BaseModel):
    incident_group_id: str
    incident_id: str | None = None
    source: EvidenceSource | str
    type: str
    summary: str = ""
    content: dict[str, Any] = Field(default_factory=dict)
    score: float | None = None
    occurred_at: datetime | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class EvidenceRecord(EvidenceCreate):
    id: str
    created_at: datetime | None = None

