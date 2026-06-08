"""Pydantic contracts for the Incident pipeline."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field


class AlertStatus(StrEnum):
    FIRING = "firing"
    RESOLVED = "resolved"


class IncidentStatus(StrEnum):
    OPEN = "open"
    MITIGATED = "mitigated"
    CLOSED = "closed"
    SUPPRESSED = "suppressed"


class DiagnosisMode(StrEnum):
    FAST = "fast"
    DEEP = "deep"


class DiagnosisTaskStatus(StrEnum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    CANCELLED = "cancelled"


class AgentRunStatus(StrEnum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    TIMEOUT = "timeout"
    CANCELLED = "cancelled"


class EvidenceSource(StrEnum):
    ALERT = "alert"
    LOG = "log"
    METRIC = "metric"
    TRACE = "trace"
    RUNBOOK = "runbook"
    INCIDENT_HISTORY = "incident_history"
    RCA = "rca"
    MCP_TOOL_RESULT = "mcp_tool_result"
    HUMAN_FEEDBACK = "human_feedback"


class NormalizedAlert(BaseModel):
    """Canonical alert shape stored before correlation."""

    id: str
    idempotency_key: str
    fingerprint: str
    status: AlertStatus = AlertStatus.FIRING
    alertname: str
    severity: str = "warning"
    service: str = ""
    instance: str = ""
    receiver: str = ""
    group_key: str = ""
    labels: dict[str, Any] = Field(default_factory=dict)
    annotations: dict[str, Any] = Field(default_factory=dict)
    raw_payload: dict[str, Any] = Field(default_factory=dict)
    query: str = ""
    starts_at: datetime | None = None
    ends_at: datetime | None = None


class IncidentIngestResult(BaseModel):
    """Result returned by the ingestion + correlation layer."""

    alert_id: str
    incident_group_id: str
    incident_id: str
    correlation_key: str
    task_id: str
    task_created: bool


class DiagnosisTaskRecord(BaseModel):
    id: str
    incident_group_id: str
    incident_id: str
    status: DiagnosisTaskStatus
    priority: int = 100
    diagnosis_mode: DiagnosisMode = DiagnosisMode.FAST
    queue_message_id: str = ""
    attempts: int = 0
    max_attempts: int = 3
    payload: dict[str, Any] = Field(default_factory=dict)
    error: str = ""
    created_at: datetime | None = None
    updated_at: datetime | None = None
    claimed_at: datetime | None = None
    finished_at: datetime | None = None


class AgentDefinition(BaseModel):
    """Industrial Agent contract: more than a prompt."""

    name: str
    version: str = "v1"
    role: str
    allowed_tools: list[str] = Field(default_factory=list)
    read_only: bool = True
    timeout_sec: int = 60
    max_retries: int = 1
    max_tokens: int = 4000
    max_evidence: int = 20
    concurrency_group: str = "llm"


class AgentEvent(BaseModel):
    """Structured event emitted by Agent Runtime and Workers."""

    type: str
    task_id: str = ""
    incident_group_id: str = ""
    agent_name: str = ""
    message: str = ""
    data: dict[str, Any] = Field(default_factory=dict)

