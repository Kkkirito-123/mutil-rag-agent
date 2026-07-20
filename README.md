# Multi-Agent AIOps Platform V3

![Python](https://img.shields.io/badge/Python-3.12-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115%2B-green)
![LangGraph](https://img.shields.io/badge/LangGraph-1.x-orange)
![Milvus](https://img.shields.io/badge/Milvus-2.4-purple)
![MCP](https://img.shields.io/badge/MCP-Tools-black)

> [!IMPORTANT]
> ### 项目定位与维护状态
>
> 本项目主要用于学习和理解基础的 **Agent Workflow** 与 **RAG** 使用方式，适合作为多智能体
> 应用的入门示例。你可以通过本项目了解任务如何在不同 Agent 之间流转、RAG 如何完成知识
> 检索与上下文补充，以及工具调用、结果汇总和诊断报告生成等基本流程。
>
> 项目同时提供了 **Skills** 的基础用法：将特定领域的角色、步骤、工具权限和输出要求组织成
> 可复用的 Skill，并由路由器根据任务选择合适的 Skill。Skills 采用**渐进式披露**思路——
> 路由阶段只向模型提供简短的名称和用途，任务真正命中后才把完整 Playbook 和工具约束加入
> 执行上下文，从而减少无关信息，让 Agent 更专注于当前任务。
>
> 本仓库仅用于个人学习、技术演示和入门参考，不建议直接用于生产环境。**当前项目已停止更新**；
> 后续会在[我的 GitHub 仓库](https://github.com/Kkkirito-123?tab=repositories)中发布重新整理的
> 新项目，带来更清晰的工程结构和更完整的 Agent 实践。新项目很快就来，敬请关注。

---

面向 OnCall / SRE 场景的多智能体诊断工作台。系统把用户故障描述或 Alertmanager 告警转换为
结构化任务，选择对应 Skill，通过 RAG 与 MCP 工具收集证据，并输出可追溯的 Markdown 报告。

V3 在原有单次诊断链路上增加了 `fast / deep` 双模式、Redis Streams 队列、后台 Worker、
Postgres 事实库、事件中心、权限与审批结构、LLM Wiki、RAG 评测和并发压测。

[项目视频](https://www.bilibili.com/video/BV182RCBGEod/)

![Product Preview](intro.png)

## 核心能力

| 能力 | 当前实现 |
| --- | --- |
| Skill-first 诊断 | 先选择主机资源、网络、容器或通用 OnCall Playbook，再收窄工具范围 |
| fast / deep 双模式 | fast 走 Plan-Execute-Replan；deep 走隔离专业 Agent 的证据图 |
| 后台任务链路 | API 快速落库和入队，多个 Worker 通过 Redis Streams 后台消费 |
| 事实与证据审计 | Postgres 保存事件、任务、AgentRun、ToolCall、Evidence、Approval 和 Report |
| RAG 检索 | Parent-Child 切分、Milvus 向量召回、BM25、RRF 融合和可选 Rerank |
| MCP 工具 | 系统、联网搜索、Windows 日志、网络和 Docker 工具独立运行 |
| 权限边界 | PermissionMode、ToolMeta、Guardrail 和人工审批共同约束副作用 |
| 可量化验证 | 检索/RAG 评测集、并发测试脚本和历史压测报告 |

## 架构概览

```mermaid
flowchart TD
    User["用户 / Alertmanager"] --> API["FastAPI API"]
    API --> Sync["同步 SSE"]
    API --> Facts[("Postgres")]
    API --> Queue[("Redis Streams")]
    Queue --> Workers["Background Workers"]
    Sync --> Runner["Diagnosis Runner"]
    Workers --> Runner
    Runner --> Fast["fast graph"]
    Runner --> Deep["deep graph"]
    Fast --> RAG["Milvus RAG"]
    Deep --> RAG
    Fast --> Tools["MCP / local tools"]
    Deep --> Tools
    Runner --> Evidence["Evidence / Report / Wiki"]
```

| 模式 | 流程 | 适合场景 |
| --- | --- | --- |
| `fast` | Skill Router → Planner → Executor → Replanner → Report | 快速排查、单类故障、即时 SSE |
| `deep` | Context → Evidence Plan → 专业 Agent 并行取证 → RCA → Report | 复杂事件、多类证据交叉验证 |

deep 当前包含 MetricAgent、LogAgent、InfraAgent 和 RunbookAgent。Agent 之间不共享中间推理，
只把压缩后的 Evidence 写回公共状态。完整实现和已知限制见[系统架构](docs/ARCHITECTURE.md)。

## 快速开始

### 1. 前置条件

- Docker 与 Docker Compose
- Python 3.12（与 `Dockerfile` 保持一致）
- 一个可用的 Chat Model Provider，例如 DeepSeek 或 DashScope
- 一个可用的 Embedding Provider：默认示例使用 Ollama + `bge-m3`，也可以改用 DashScope

### 2. 获取代码与安装依赖

```bash
git clone https://github.com/Kkkirito-123/mutil-rag-agent.git
cd mutil-rag-agent

python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Windows PowerShell 激活虚拟环境：

```powershell
.\.venv\Scripts\Activate.ps1
```

### 3. 配置 Provider

编辑 `.env`，至少完成以下配置：

- Chat Model 名称与 API Key 使用同一个 Provider。
- 使用本地 Embedding 时，先运行 `ollama pull bge-m3`。
- 使用 DashScope Embedding 时，将 `EMBEDDING_PROVIDER` 改为 `dashscope` 并配置
  `DASHSCOPE_API_KEY`。
- 将 `KB_ADMIN_TOKEN` 改成仅自己知道的值。

项目会根据模型名称选择 Chat Provider：以 `deepseek` 开头的模型使用 `DEEPSEEK_API_KEY`，
其他示例模型使用 DashScope 配置。不要把真实 Key 提交到 Git。

### 4. 启动基础设施

```bash
docker compose up -d
docker compose ps
```

这会启动 Milvus、Redis、Postgres、Attu 和 open-webSearch，以及 Milvus 依赖的 etcd 与 MinIO。

### 5. 导入知识库

先检查待导入内容，再执行重建：

```bash
python scripts/ingest_kb_corpus.py --dry-run
python scripts/ingest_kb_corpus.py --reset --batch 8
```

默认公开语料包含 954 条 Prometheus 告警文档和通用/Redis/MySQL OnCall SOP。
`scripts/convert_log_templates.py` 可从用户自行准备的 loghub-2.0 数据生成额外日志模板；
默认仓库不包含这些模板。

### 6. 启动应用

推荐使用完整容器栈：

```bash
docker compose --profile app up -d --build
docker compose --profile app logs -f api worker-1
```

macOS / Linux 也可以使用容器基础设施加本地 Python 进程：

```bash
bash scripts/run_all.sh
```

Windows 完整 V3 拓扑建议继续使用 Compose `app` Profile。`run.ps1` 是本地兼容入口，
不会启动完整的 Postgres/后台 Worker 拓扑。

停止服务：

```bash
docker compose --profile app down
```

使用本地脚本启动时：

```bash
bash scripts/stop_all.sh --infra
```

### 7. 检查就绪状态

```bash
curl -fsS http://localhost:9900/api/v1/health/ready
```

## 访问入口

| 页面或接口 | 地址 |
| --- | --- |
| Web UI | <http://localhost:9900> |
| Swagger | <http://localhost:9900/docs> |
| ReDoc | <http://localhost:9900/redoc> |
| 健康检查 | <http://localhost:9900/api/v1/health> |
| 就绪检查 | <http://localhost:9900/api/v1/health/ready> |
| 队列状态 | <http://localhost:9900/api/v1/queue/status> |
| Attu Milvus UI | <http://localhost:8000> |

## 使用示例

本机资源诊断：

```text
我电脑很卡，帮我检查 CPU、内存、磁盘和高占用进程。
```

复杂告警诊断：

```text
Redis 实例 redis-master-01 内存使用率 98%，客户端连接被强制断开，请用 deep 模式交叉取证。
```

模拟 Alertmanager Webhook：

```bash
python scripts/mock_alert.py --scenario redis
python scripts/mock_alert.py --list-history
```

压测命令可能创建真实任务或调用 LLM。先阅读[并发测试指南](docs/CONCURRENCY_TEST_GUIDE.md)，
并从较小的 `--n` 开始。

## 主要 API

| 功能 | 方法 | 路径 |
| --- | --- | --- |
| 同步 SSE 诊断 | POST | `/api/v1/aiops/diagnose` |
| 后台诊断提交 | POST | `/api/v1/aiops/diagnose/submit` |
| Alertmanager Webhook | POST | `/api/v1/webhook/alertmanager` |
| 队列与 Worker 状态 | GET | `/api/v1/queue/status` |
| 诊断任务列表 | GET | `/api/v1/incidents/tasks` |
| RAG Chat | POST | `/api/v1/chat/stream` |
| Skill 列表 | GET | `/api/v1/skills` |
| 上传知识文档 | POST | `/api/v1/documents/upload` |
| 就绪检查 | GET | `/api/v1/health/ready` |

知识库上传和删除需要请求头：

```http
X-KB-Admin-Token: your-admin-token
```

完整请求结构以运行中的 OpenAPI 文档为准。

## 项目结构

```text
.
├── app/
│   ├── agents/              # fast 节点和 deep 专业 Agent
│   ├── api/                 # FastAPI 路由
│   ├── diagnosis_graphs/    # deep graph
│   ├── orchestration/       # 诊断执行与审计
│   ├── runtime/             # Harness、权限、审批和工具编排
│   ├── skills/              # Skill 注册表与 Playbook
│   ├── incidents/           # 事件与任务事实
│   ├── queue/               # Redis Streams
│   └── core/                # LLM、Milvus、Embedding、Rerank 等基础能力
├── benchmark/               # 检索与 RAG 评测
├── data/kb_corpus/          # 公开 RAG 语料
├── docs/                    # 架构、并发验证、压测和 SOP
├── frontend/                # Web UI
├── mcp_servers/             # MCP 工具服务
├── open-webSearch-main/     # 第三方本地搜索服务
└── scripts/                 # 启动、导入、告警模拟与压测脚本
```

## 文档导航

- [系统架构与已知限制](docs/ARCHITECTURE.md)
- [Skill 层与扩展方式](app/skills/README.md)
- [Benchmark 使用说明](benchmark/README.md)
- [并发与队列测试指南](docs/CONCURRENCY_TEST_GUIDE.md)
- [历史压测报告](docs/PRESSURE_TEST_REPORT.md)
- [Redis On-Call SOP](docs/sop/redis_oncall_sop.md)
- [MySQL On-Call SOP](docs/sop/mysql_oncall_sop.md)
- [通用告警处理手册](docs/sop/common_alerts.md)
- [AI 编码 Agent 仓库规则](AGENTS.zh-CN.md)

历史压测数据只代表报告记录的机器、配置和时间点，不是其他部署环境的性能保证。

## 数据、安全与费用

- 不提交 `.env`、API Key、真实私有端点、数据库卷、日志或运行时 Wiki。
- MCP system/network/docker 工具可能读取宿主机或网络信息；只在授权环境中运行。
- Docker MCP 包含受控重启能力，高风险工具默认阻断，不应使用 `PERMISSION_MODE=bypass`
  暴露到公网。
- `ragas`、真实诊断、远程 Embedding、Rerank 和联网搜索可能产生费用或发送数据到外部服务。
- 当前 CORS 允许所有来源，适合本地演示；生产部署必须增加身份认证、来源限制和反向代理策略。

## 版本说明

“V3”表示项目架构的第三代演进：从同步演示链路升级为带后台队列、事实审计和双诊断图的工作台。
运行时 API 版本仍由 `.env` 中的 `APP_VERSION` 独立配置。

## License 与来源

本项目代码以 [MIT License](LICENSE) 发布。

仓库包含或参考以下第三方资产，其许可证分别生效：

- [Aas-ee/open-webSearch](https://github.com/Aas-ee/open-webSearch)：本地联网搜索服务，仓库副本位于
  `open-webSearch-main/`，采用 Apache License 2.0。
- [samber/awesome-prometheus-alerts](https://github.com/samber/awesome-prometheus-alerts)：
  Prometheus 告警语料来源，原始项目标注为 CC BY 4.0。

具体权利与义务以各项目的官方许可证原文为准。
