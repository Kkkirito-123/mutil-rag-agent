# Repository Guide for AI Coding Agents

This file is the repository-wide source of truth and current operational map for
Codex, Claude Code, Kimi Code, and other coding agents. `AGENTS.zh-CN.md` is the
synchronized human-facing Chinese translation. `CLAUDE.md` imports this file for
Claude Code.

## 1. Authority and Working Contract

- Read this file and any nearer `AGENTS.md` before acting in a subtree. A nearer
  guide may add subtree-specific commands or constraints but may not weaken root
  rules.
- Source and executable checks describe current behavior. Approved designs
  describe intended behavior. Report drift instead of silently choosing one.
- Reply in Chinese unless the user requests another language. Keep source
  identifiers, API names, and test names in English. Match the surrounding
  language for comments and docstrings; Chinese user-facing text is part of the
  current product behavior.
- Read the owning implementation, contracts, documentation, and relevant checks
  before editing. Keep one change focused on one approved objective.
- Preserve user work. Do not overwrite, revert, delete, stage, or publish
  unrelated changes.
- Before a feature, refactor, deletion, dependency or schema change, batch edit,
  global configuration change, new top-level directory, or other high-impact
  change, present the goal, users or stakeholders, MVP, non-goals, file scope,
  acceptance criteria, and risks or tradeoffs for approval.
- Never expose credentials or private endpoints in source, command arguments,
  fixtures, logs, screenshots, manifests, or results. Confirm scope before an
  external write or irreversible action.

## 2. Repository Profile

This repository is a personal, public reference implementation of a multi-agent
AIOps diagnosis workbench for OnCall and SRE scenarios. It accepts user reports
or Alertmanager events, selects a Skill playbook, gathers evidence through RAG
and MCP tools, and emits traceable Markdown reports.

The current product generation is called **V3**. V3 adds a background task
pipeline, Redis Streams, worker processes, Postgres facts, fast/deep diagnosis
modes, evidence audit records, approval structures, an LLM Wiki, retrieval
evaluation, and concurrency testing. It is a reference implementation, not a
claim of production readiness.

Primary stakeholder: the repository owner and maintainer. Secondary stakeholders
are users who run the demo and contributors who need reproducible project facts.

### Keep this map current

This guide describes how the repository works now; it is not a changelog,
backlog, or copy of every implementation detail. Update the relevant root or
module guide in the same change when code changes the top-level layout, module
ownership, service topology, primary flow or entry point, dependency direction,
public protocol, compatibility or security boundary, canonical command, or
validation requirement.

Do not churn this guide for an internal refactor or small bug fix that leaves
those facts unchanged. Update `README.md` for user-facing setup or behavior. Keep
durable detail that cannot fit this orientation map in
`docs/ARCHITECTURE.md`, and link instead of duplicating it.

### Verified stack

- Python 3.12 is the container baseline (`Dockerfile`). The repository has no
  package metadata declaring a wider supported Python range.
- FastAPI and Uvicorn provide the HTTP/SSE application.
- LangGraph runs the fast and deep diagnosis graphs.
- Milvus stores vectors; Redis stores queue/runtime coordination; Postgres stores
  incident and diagnosis facts.
- MCP services expose system, web search, Windows event log, network, and Docker
  tools.
- `open-webSearch-main/` is a vendored Apache-2.0 third-party project with its own
  Node.js build and documentation.

## 3. Canonical Setup and Commands

Create local configuration before commands that load Compose application
services:

```bash
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Configure model credentials and an embedding provider in `.env`. Model names and
API keys must use the same provider. Never commit `.env`.

Infrastructure only:

```bash
docker compose up -d
```

Complete containerized stack (API, three workers, MCP services, and
infrastructure):

```bash
docker compose --profile app up -d --build
```

Local macOS/Linux stack with containerized infrastructure and local Python
processes:

```bash
bash scripts/run_all.sh
bash scripts/stop_all.sh
```

The Windows `run.ps1` launcher is a local compatibility entry point. It does not
start the complete V3 Postgres/worker topology; use the Compose `app` profile for
the full stack.

Knowledge-base ingestion and evaluation:

```bash
python scripts/ingest_kb_corpus.py --dry-run
python scripts/ingest_kb_corpus.py --reset --batch 8
python benchmark/run_benchmark.py retrieval --k 3
python benchmark/run_benchmark.py ragas --limit 5
```

`ragas`, real diagnosis, ingestion with remote embeddings, and some health checks
may call paid or external providers. Do not run them merely as a static quality
gate; confirm credentials, cost, data scope, and service readiness first.

## 4. Information and Directory Ownership

| Path | Primary responsibility |
| --- | --- |
| `README.md` | User value, prerequisites, quick start, entry points, and documentation index |
| `docs/ARCHITECTURE.md` | Current architecture, runtime boundaries, safety boundaries, and known limitations |
| `docs/CONCURRENCY_TEST_GUIDE.md` | Reproducible queue, rate-limit, and concurrency checks |
| `docs/PRESSURE_TEST_REPORT.md` | Historical environment-specific pressure-test evidence |
| `app/api/` | HTTP/SSE ingress and request/response contracts |
| `app/services/` | Use-case services such as diagnosis and RAG chat |
| `app/orchestration/` | Diagnosis-mode selection, execution, audit, and event conversion |
| `app/agents/` | Fast graph nodes and deep specialist agents |
| `app/diagnosis_graphs/` | Deep diagnosis graph assembly and evidence reduction |
| `app/runtime/` | Agent harness, permissions, approvals, tool orchestration, budgets, and transitions |
| `app/skills/` | Skill models, loader, registry, playbooks, and Skill documentation |
| `app/tools/`, `mcp_servers/` | Tool metadata, local tools, and external MCP process boundaries |
| `app/incidents/`, `app/evidence/`, `app/db/` | Incident, evidence, persistence, and schema ownership |
| `app/queue/` | Redis Streams, worker coordination, and queue observability |
| `app/core/`, `app/rag/` | Provider clients, embeddings, retrieval, reranking, and shared infrastructure |
| `benchmark/` | Retrieval/RAG evaluation datasets, runner, and generated reports |
| `data/kb_corpus/` | Versioned public RAG corpus; not operational documentation |
| `data/wiki/` | Runtime-generated experience store; only conventions are versioned |
| `frontend/` | Static Web UI served by FastAPI |
| `open-webSearch-main/` | Vendored third-party search service; keep changes isolated |

Do not duplicate the same facts across README, architecture, benchmark, and
pressure-test documents. Link to the owning document instead.

## 5. Architecture and Safety Boundaries

See `docs/ARCHITECTURE.md` for the detailed runtime and data flow. The following
are the compact boundaries an agent must preserve while editing:

- The API accepts and validates work. High-concurrency diagnosis should be
  persisted and queued instead of executed synchronously in the request process.
- `fast` uses Skill Router -> Planner -> Executor -> Replanner -> Report.
- `deep` uses incident context -> evidence plan -> isolated specialist fan-out ->
  evidence reduction -> RCA -> remediation proposal -> report.
- Specialist agents return compressed Evidence. Their private intermediate LLM
  conversation must not become shared graph state.
- Postgres is the fact authority for alerts, groups, tasks, agent runs, tool
  calls, evidence, approvals, and reports. Redis owns transient queue and
  coordination state, not durable facts.
- Observable state and explicit evidence determine completion. Model text alone
  is not proof that a tool, task, or remediation succeeded.
- Tool execution must retain the Skill, permission, guardrail, approval, and
  audit boundaries. Read-only tools may be added by runtime policy; write,
  notification, and high-risk tools require explicit authorization.
- `PERMISSION_MODE=bypass` is development-only. Do not recommend it for a public
  or production deployment.
- Retryable side effects require idempotency or an explicit uncertain-outcome
  recovery path. Queue acknowledgement, retries, pending recovery, and DLQ
  behavior must remain distinguishable.
- Do not move provider-specific behavior into API routes. Keep ingress, use-case,
  orchestration, runtime, and provider boundaries distinct.

## 6. Sensitive Areas

Changes in these areas require focused evidence and usually separate approval:

- `.env.example` and `app/config.py`: provider selection, credentials, public
  endpoints, concurrency, and security defaults.
- `app/runtime/permissions.py`, `tool_filter.py`, `tool_runner.py`, and
  `approvals.py`: public safety and side-effect boundaries.
- `mcp_servers/docker_server.py`: contains a restart operation. Never treat every
  Docker tool as read-only.
- `app/db/postgres.py`: schema and persistence compatibility.
- `app/queue/`, distributed limiter, rate limiter, worker recovery, and DLQ:
  concurrency and duplicate-execution risk.
- `data/wiki/`: may contain runtime incident information and must remain ignored.
- Benchmark and pressure tests: may create tasks, write facts, call providers, or
  incur cost. Use small inputs first and clean only test-scoped data.
- `open-webSearch-main/`: third-party source under its own license and toolchain.

## 7. Validation Expectations

The repository currently has no committed `tests/` suite, `pyproject.toml`, or CI
workflow. Do not claim unit, integration, or end-to-end coverage that does not
exist.

Safe baseline checks:

```bash
ruff check app mcp_servers benchmark scripts
python -m compileall -q app mcp_servers benchmark scripts
docker compose config --quiet
git diff --check
```

For Markdown changes, also verify local links, code-fence balance, paths, commands,
and that historical results remain labeled as environment-specific evidence.

The current repository predates a shared formatter configuration. A blanket
`ruff format` or `black` pass produces a large unrelated diff. Do not mass-format
without an approved formatting-only change and a pinned configuration.

Runtime validation, when credentials and services are explicitly in scope:

```bash
curl -fsS http://localhost:9900/api/v1/health/ready
python scripts/loadtest.py status
python benchmark/run_benchmark.py retrieval --k 3
```

State exactly what was exercised. Static checks and mocks do not prove provider,
database, network, MCP, or end-to-end behavior.

## 8. Git and Delivery

- Start substantive work from an up-to-date default branch and use a focused
  branch for substantive changes.
- Stage only files belonging to the approved objective. Inspect the final diff
  for secrets, generated artifacts, unrelated formatting, compatibility breaks,
  and accidental public APIs.
- Keep the default branch runnable. Prefer a Draft PR while validation gates or
  design questions remain.
- Do not rewrite shared history or delete user data without explicit approval and
  a recovery plan.

A completion report states what changed, which files changed, validation,
discoveries, remaining risks, and any genuinely reusable lesson. Completion must
come from evidence, not prose or a process exit code alone.
