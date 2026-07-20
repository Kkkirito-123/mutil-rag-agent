# AI 编码 Agent 仓库指南

本文件是仓库级操作规则的简体中文同步译文，适用于 Codex、Claude Code、Kimi Code
等编码 Agent。英文 `AGENTS.md` 是操作权威，`CLAUDE.md` 为 Claude Code 导入该文件。

## 1. 权威与工作契约

- 执行仓库操作前先阅读本文件。更近的 `AGENTS.md` 可以补充子树专属命令和约束，
  但不能削弱根规则。
- 源码和可执行检查说明当前行为，已批准设计说明预期行为；发现漂移时必须报告，
  不能静默任选一个版本。
- 默认使用中文回复，除非用户要求其他语言。源码标识符、API 名称和测试名使用英文；
  注释与 Docstring 跟随所属文件的现有语言风格，中文用户界面文案属于当前产品行为。
- 编辑前阅读所属实现、契约、文档和相关检查；每次修改只服务一个已批准目标。
- 保护用户工作，不覆盖、回滚、删除、暂存或发布无关修改。
- 新功能、重构、删除、依赖或 Schema 变更、批量编辑、全局配置变化、新顶层目录或其他
  高影响修改前，先提交计划并等待确认。
- 计划必须说明目标、用户或干系人、MVP、非目标、文件范围、验收标准和风险取舍。
- 不在源码、命令参数、Fixture、日志、截图、清单或结果中暴露凭证和私有地址；外部写入
  或不可逆动作前确认范围。

## 2. 仓库画像

本仓库是个人维护、公开发布的多智能体 AIOps 诊断工作台参考实现，面向 OnCall / SRE
场景。系统接收用户故障描述或 Alertmanager 事件，选择 Skill 排障剧本，通过 RAG 和 MCP
工具收集证据，并输出可追溯的 Markdown 报告。

当前产品代际称为 **V3**。V3 增加后台任务链路、Redis Streams、Worker、Postgres 事实库、
fast/deep 双诊断模式、证据审计、审批结构、LLM Wiki、检索评测和并发测试。它是参考实现，
不等同于生产就绪承诺。

主要干系人是仓库所有者和维护者；次要干系人是运行演示的使用者，以及需要可复现项目事实的
贡献者。

### 已验证技术栈

- 容器基线是 Python 3.12（见 `Dockerfile`）。仓库没有声明更宽 Python 兼容范围的包元数据。
- FastAPI 和 Uvicorn 提供 HTTP/SSE 应用。
- LangGraph 执行 fast 与 deep 诊断图。
- Milvus 保存向量，Redis 保存队列和运行态协调，Postgres 保存事件与诊断事实。
- MCP 服务提供系统、联网搜索、Windows 事件日志、网络和 Docker 工具。
- `open-webSearch-main/` 是采用 Apache-2.0 的第三方内嵌项目，拥有独立 Node.js 构建和文档。

## 3. 标准安装与命令

运行会加载 Compose 应用服务的命令前，先创建本地配置：

```bash
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

在 `.env` 中配置模型凭证和 Embedding Provider。模型名与 API Key 必须属于同一 Provider。
绝不能提交 `.env`。

只启动基础设施：

```bash
docker compose up -d
```

启动完整容器栈（API、三个 Worker、MCP 服务和基础设施）：

```bash
docker compose --profile app up -d --build
```

macOS/Linux 使用容器基础设施与本地 Python 进程：

```bash
bash scripts/run_all.sh
bash scripts/stop_all.sh
```

Windows `run.ps1` 是本地兼容入口，不会启动完整 V3 Postgres/Worker 拓扑；完整环境应使用
Compose 的 `app` Profile。

知识库导入与评测：

```bash
python scripts/ingest_kb_corpus.py --dry-run
python scripts/ingest_kb_corpus.py --reset --batch 8
python benchmark/run_benchmark.py retrieval --k 3
python benchmark/run_benchmark.py ragas --limit 5
```

`ragas`、真实诊断、远程 Embedding 导入和部分健康检查可能调用付费或外部 Provider。
不要把它们当作普通静态质量门直接运行；先确认凭证、费用、数据范围和服务就绪状态。

## 4. 信息与目录归属

| 路径 | 主要职责 |
| --- | --- |
| `README.md` | 用户价值、前置条件、快速开始、使用入口和文档索引 |
| `docs/ARCHITECTURE.md` | 当前架构、运行边界、安全边界和已知限制 |
| `docs/CONCURRENCY_TEST_GUIDE.md` | 可复现的队列、限流和并发检查 |
| `docs/PRESSURE_TEST_REPORT.md` | 特定历史环境下的压测证据 |
| `app/api/` | HTTP/SSE 入口和请求响应契约 |
| `app/services/` | 诊断、RAG Chat 等用例服务 |
| `app/orchestration/` | 诊断模式选择、执行、审计和事件转换 |
| `app/agents/` | fast 图节点和 deep 专业 Agent |
| `app/diagnosis_graphs/` | deep 诊断图装配与证据归并 |
| `app/runtime/` | Agent Harness、权限、审批、工具编排、预算和状态转换 |
| `app/skills/` | Skill 模型、加载器、注册表、Playbook 和 Skill 文档 |
| `app/tools/`、`mcp_servers/` | 工具元数据、本地工具和外部 MCP 进程边界 |
| `app/incidents/`、`app/evidence/`、`app/db/` | 事件、证据、持久化和 Schema |
| `app/queue/` | Redis Streams、Worker 协调和队列可观测性 |
| `app/core/`、`app/rag/` | Provider 客户端、Embedding、检索、Rerank 和共享基础设施 |
| `benchmark/` | 检索/RAG 评测数据集、运行器和生成报告 |
| `data/kb_corpus/` | 版本化公开 RAG 语料，不是运维文档 |
| `data/wiki/` | 运行时经验库，只提交约定文件 |
| `frontend/` | FastAPI 提供的静态 Web UI |
| `open-webSearch-main/` | 第三方内嵌搜索服务，修改必须独立隔离 |

不要在 README、架构文档、Benchmark 和压测报告之间重复同一事实；应链接到信息所有者。

## 5. 架构与安全不变量

- API 负责接入和校验。高并发诊断应先持久化并入队，不能长期占用请求进程执行。
- `fast` 使用 Skill Router -> Planner -> Executor -> Replanner -> Report。
- `deep` 使用事件上下文 -> 证据计划 -> 隔离专业 Agent 扇出 -> 证据归并 -> RCA ->
  处置建议 -> 报告。
- 专业 Agent 只返回压缩后的 Evidence，私有 LLM 中间对话不能写入共享图状态。
- Postgres 是 alerts、groups、tasks、agent runs、tool calls、evidence、approvals 和 reports
  的事实权威。Redis 负责临时队列和协调状态，不是持久事实库。
- 可观察状态和明确证据决定完成；模型文本本身不能证明工具、任务或处置已经成功。
- 工具执行必须保留 Skill、Permission、Guardrail、审批和审计边界。只读工具可由运行时
  策略补充；写入、通知和高风险工具需要明确授权。
- `PERMISSION_MODE=bypass` 只允许开发使用，不能推荐给公开或生产部署。
- 可重试副作用必须具备幂等性，或明确的不确定结果恢复路径。队列 ACK、重试、Pending
  回收和 DLQ 必须保持可区分。
- Provider 专属行为不能塞进 API 路由；入口、用例、编排、运行时和 Provider 边界应保持分离。

## 6. 敏感区域

以下区域的修改需要聚焦证据，通常还需单独确认：

- `.env.example` 与 `app/config.py`：Provider 选择、凭证、公共端点、并发和安全默认值。
- `app/runtime/permissions.py`、`tool_filter.py`、`tool_runner.py` 和 `approvals.py`：
  对外安全与副作用边界。
- `mcp_servers/docker_server.py`：包含重启操作，不能把所有 Docker 工具视为只读。
- `app/db/postgres.py`：Schema 与持久化兼容性。
- `app/queue/`、分布式并发槽、限流器、Worker 恢复和 DLQ：并发与重复执行风险。
- `data/wiki/`：可能包含运行时事件信息，必须继续保持忽略。
- Benchmark 与压测：可能创建任务、写事实库、调用 Provider 或产生费用。先用小输入，
  且只清理测试范围数据。
- `open-webSearch-main/`：第三方源码，采用独立许可证和工具链。

## 7. 验证要求

仓库目前没有已提交的 `tests/` 测试套件、`pyproject.toml` 或 CI Workflow。不能声称不存在的
单元、集成或端到端覆盖率。

安全基线检查：

```bash
ruff check app mcp_servers benchmark scripts
python -m compileall -q app mcp_servers benchmark scripts
docker compose config --quiet
git diff --check
```

修改 Markdown 时还要检查本地链接、代码围栏、路径和命令，并确保历史测试结果仍明确标注为
特定环境证据。

仓库早于统一 Formatter 配置。全量执行 `ruff format` 或 `black` 会产生巨大无关 Diff；
没有单独批准的格式化任务和固定配置时，不得批量格式化。

当凭证和服务明确纳入范围时，可运行：

```bash
curl -fsS http://localhost:9900/api/v1/health/ready
python scripts/loadtest.py status
python benchmark/run_benchmark.py retrieval --k 3
```

必须准确说明实际验证范围。静态检查和 Mock 不能证明 Provider、数据库、网络、MCP 或端到端行为。

## 8. Git 与交付

- 实质工作从已同步的默认分支开始，并为实质性修改使用范围明确的分支。
- 只暂存已批准目标中的文件。最终检查 Diff 中的密钥、生成物、无关格式化、兼容性破坏和
  意外公共 API。
- 保持默认分支可运行；验证 Gate 或设计问题未收敛时优先使用 Draft PR。
- 没有明确批准和恢复计划时，不改写共享历史，不删除用户数据。

完成报告必须说明修改内容、文件、验证、发现、剩余风险和确有价值的可复用经验。完成必须来自
证据，不能只依赖文字或进程退出码。
