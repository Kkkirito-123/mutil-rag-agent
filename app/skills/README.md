# Skill 层

Skill 是 OnCall Agent 的 **故障处理剧本** (Playbook), 把"怎么排障"从 Prompt 中解耦, 沉淀为可复用、可版本管理的资产。

## 与 Tool / RAG / LangGraph 的关系

| 层级 | 职责 |
|------|------|
| **Tool** | 单个具体能力 (查本机状态 / 查事件日志 / 网络探测 / 查知识库) |
| **RAG** | 知识检索, 是 Tool 的一种 (`search_knowledge_base`) |
| **Skill** | 面向某类故障的方法论, 编排 Tool 调用顺序与输出格式 |
| **LangGraph** | 流程编排器 (Skill Router → Planner → Executor → Replanner) |

> **Skill 不是 Tool, 不是 Prompt, 也不是 Workflow.**
> Skill 是"针对某类故障, 用什么思路、调什么工具、按什么顺序、输出什么格式"的剧本。

## 文件布局

```
app/
  agents/
    skill_router.py                 # Skill Router LangGraph 节点
  skills/
    models.py                       # Skill 数据模型
    loader.py                       # SKILL.md 解析器
    registry.py                     # SkillRegistry 单例
    definitions/
      host_resource_diagnosis/SKILL.md # CPU/内存/磁盘/本机卡顿
      network_diagnosis/SKILL.md       # 网络问题 (ping/HTTP/DNS/端口)
      container_diagnosis/SKILL.md     # Docker 容器异常
      generic_oncall/SKILL.md          # 兜底, 必须存在
```

当前公开版保留 4 个内置 Skill:

| Skill | 说明 |
|---|---|
| `host_resource_diagnosis` | 主机 CPU、内存、磁盘、OOM、本机卡顿等资源类故障 |
| `network_diagnosis` | 网站打不开、接口超时、DNS 异常、端口不通等网络问题 |
| `container_diagnosis` | Docker 容器异常、重启循环、资源占用高、启动失败 |
| `generic_oncall` | 无法归类或多组件复合问题的通用兜底剧本 |

早期实验性 Skill 已从公开版移除。当前版本优先保留本地可运行、可验证、工具边界清楚的 OnCall 场景。


## SKILL.md 格式

YAML frontmatter + Markdown body:

```markdown
---
name: cpu_high_usage             # 唯一标识, 支持 snake_case / kebab-case
display_name: CPU 高使用率排查    # 人类可读名
description: 主机/容器 CPU 持续高负载...   # 给 Router 看的一句话
category: oncall                 # 可选, 也兼容 metadata.hermes.category
platforms: [windows, linux]      # 可选, 不填表示全平台
tags: [cpu, host]                # 可选, 也兼容 metadata.hermes.tags
triggers:                         # 触发关键词 (Router 启发式参考)
  - cpu 高
  - cpu 100
allowed_tools:                    # 允许 Executor 调用的工具白名单 (Harness 强制)
  - search_knowledge_base         # 知识库 RAG
  - get_local_cpu_memory          # 本机 psutil
risk_level: low                   # low / medium / high
---

# CPU 高使用率排查 Playbook

## 适用场景
- ...

## 推荐排查步骤
1. ...

## 输出重点
- ...

## 注意事项
- ...
```

frontmatter 字段约束见 `models.Skill`. `display_name` 可省略, 会从 `title`、Markdown H1 或目录名推导。

## Hermes-lite 兼容

当前 SkillRegistry 借鉴 Hermes 的渐进披露机制, 但不引入 hub/marketplace:

- `GET /api/v1/skills`: 返回元信息, 不含 playbook 全文
- `GET /api/v1/skills/{name}`: 返回单个 Skill 的 playbook 和支持文件索引
- `GET /api/v1/skills/{name}/files?path=references/foo.md`: 读取 Skill 目录内支持文件
- `POST /api/v1/skills/reload`: 清缓存并重新扫描

`.env` 可配置:

```env
SKILLS_EXTERNAL_DIRS=C:\path\to\hermes-skills
SKILLS_DISABLED=some-skill,experimental-skill
SKILLS_PLATFORM=windows
```

外部目录支持 Hermes/agentskills 常见结构:

```text
external-skills/
  github/
    pr-workflow/
      SKILL.md
      references/api.md
  oncall/
    mysql-incident/
      SKILL.md
```

`metadata.hermes.category`、`metadata.hermes.tags`、`platforms` 会被读取; `requires_toolsets`、远程安装、secret 注入和自动安全审计暂不实现。

## 加一个新 Skill

1. 在 `definitions/` 下新建目录 `your_skill_name/`
2. 创建 `SKILL.md`, frontmatter 字段填全
3. 在 `## 推荐排查步骤` 下用编号列表写 Playbook
4. 调 `POST /api/v1/skills/reload` 或重启进程, `SkillRegistry` 会重新加载

## 路由策略

第一版采用 **纯 LLM + structured output**:

1. 把所有 Skill 的 `name + description + triggers` 拼成菜单
2. LLM 返回 `SkillChoice(skill_name, reason)`
3. 不存在的 name / LLM 异常 → 回退到 `generic_oncall`

后续可以叠加:
- 启发式 trigger 关键词优先匹配
- 缓存路由决策, 减少 LLM 调用
- 多 Skill 并行执行 (复合故障)

## 工具白名单 (已强制)

每个 Skill 的 `allowed_tools` 字段已在 `app/runtime/tool_filter.py` 强制:

- Executor 启动时通过 `filter_tools_for_skill()` 过滤工具
- 不在白名单的工具不会暴露给 Agent (LLM 看不到, 也调不了)
- 同一个 Skill 的执行器会按 skill、工具集合、运行模式、权限模式缓存复用

风险分级 `risk_level`:
- `low`: 只读工具 (查询本机状态、看日志)
- `medium`: 写工具或可能影响 (发送通知、读取敏感事件日志)
- `high`: 危险操作 (容器重启等, 默认禁用, 需 `.env` 显式开启)
