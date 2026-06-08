"""AIOps 多智能体接口的数据模型."""

from typing import Any, Dict, Literal

from pydantic import BaseModel, Field, field_validator

from app.incidents.models import DiagnosisMode


class DiagnosisRequest(BaseModel):
    """AIOps 诊断请求."""

    session_id: str = Field(default="default", description="会话 ID")
    query: str = Field(
        ...,
        description="告警内容 / 故障现象 / 运维问题",
        min_length=1,
        max_length=4000,
    )
    diagnosis_mode: DiagnosisMode = Field(
        default=DiagnosisMode.FAST,
        description="诊断模式: fast=日常 Plan-Execute-Replan; deep=深度多 Agent 组诊断入口",
    )

    @field_validator("diagnosis_mode", mode="before")
    @classmethod
    def _normalize_diagnosis_mode(cls, value: object) -> object:
        raw = str(value or DiagnosisMode.FAST.value).strip().lower()
        aliases = {
            "daily": DiagnosisMode.FAST,
            "normal": DiagnosisMode.FAST,
            "routine": DiagnosisMode.FAST,
            "fast": DiagnosisMode.FAST,
            "日常": DiagnosisMode.FAST,
            "常规": DiagnosisMode.FAST,
            "deep": DiagnosisMode.DEEP,
            "depth": DiagnosisMode.DEEP,
            "group": DiagnosisMode.DEEP,
            "深度": DiagnosisMode.DEEP,
        }
        return aliases.get(raw, DiagnosisMode.FAST)

    model_config = {
        "json_schema_extra": {
            "example": {
                "session_id": "diag-001",
                "query": "数据库 CPU 使用率持续 100%, 已经 30 分钟, 业务受影响",
                "diagnosis_mode": "fast",
            }
        }
    }


# ============================================================
# SSE 事件 schema (仅用于 OpenAPI 文档示例, 实际 SSE 用 JSON 字符串)
# ============================================================
EventType = Literal[
    "start",           # 流程启动
    "mode_selected",   # 诊断模式已确认
    "skill_selected",  # SkillRouter 选定 Skill
    "plan",            # Planner 完成, 给出初始计划
    "step_start",      # Executor 开始单步
    "step_complete",   # Executor 完成单步
    "replan",          # Replanner 给出新计划
    "report",          # 生成最终报告
    "complete",        # 流程结束
    "error",           # 错误
]


class DiagnosisEvent(BaseModel):
    """诊断 SSE 事件 (示例 schema)."""

    type: EventType = Field(..., description="事件类型")
    stage: str = Field(..., description="阶段标识")
    message: str = Field(default="", description="人类可读的描述")
    data: Dict[str, Any] = Field(default_factory=dict, description="结构化数据载荷")
