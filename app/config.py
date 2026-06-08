"""应用配置管理.

使用 Pydantic Settings 实现:
  - 自动从 .env 加载
  - 类型校验
  - 字段说明 (可生成文档)
  - 单例模式 (整个进程共享一份配置)

设计原则:
  - 所有可变配置走 .env, 代码里不硬编码
  - 字段名小写 + 下划线 (Python 风格)
  - 环境变量大写 (POSIX 风格), 通过 case_sensitive=False 自动匹配
"""

from functools import lru_cache
from typing import Any, Dict

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """应用全局配置."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ==================== 应用基础 ====================
    app_name: str = Field(default="MultiAgentAIOps", description="应用名")
    app_version: str = Field(default="1.0.0", description="应用版本")
    debug: bool = Field(default=False, description="调试模式")
    host: str = Field(default="0.0.0.0", description="监听地址")
    port: int = Field(default=9900, description="监听端口")

    # ==================== DashScope LLM ====================
    dashscope_api_key: str = Field(default="", description="DashScope API Key")
    dashscope_base_url: str = Field(
        default="https://dashscope.aliyuncs.com/compatible-mode/v1",
        description="DashScope OpenAI 兼容模式 URL",
    )
    dashscope_chat_model: str = Field(default="qwen-max", description="Chat 模型")
    dashscope_router_model: str = Field(default="qwen-turbo", description="Router 模型")

    # ==================== DeepSeek (OpenAI 兼容) ====================
    # 当 *_chat_model / *_router_model / agent_planner_model 名字以 "deepseek" 开头时,
    # get_chat_llm 会自动切到 DeepSeek 的 base_url + api_key.
    deepseek_api_key: str = Field(default="", description="DeepSeek API Key (platform.deepseek.com)")
    deepseek_base_url: str = Field(
        default="https://api.deepseek.com",
        description="DeepSeek OpenAI 兼容 URL",
    )
    dashscope_embedding_model: str = Field(
        default="text-embedding-v4", description="Embedding 模型"
    )
    dashscope_embedding_dim: int = Field(default=1024, description="Embedding 向量维度")
    embedding_provider: str = Field(
        default="dashscope",
        description="Embedding 提供方: dashscope / ollama",
    )
    ollama_base_url: str = Field(
        default="http://localhost:11434",
        description="Ollama 本地服务地址, 用于本地 embedding",
    )
    ollama_embedding_model: str = Field(
        default="bge-m3",
        description="Ollama embedding 模型名, 推荐 bge-m3",
    )
    ollama_embedding_dim: int = Field(
        default=1024,
        description="Ollama embedding 向量维度, bge-m3 通常为 1024",
    )
    ollama_embedding_batch_size: int = Field(
        default=16,
        description="调用 Ollama /api/embed 时每批文本数量",
    )
    ollama_embedding_timeout_sec: float = Field(
        default=60.0,
        description="Ollama embedding HTTP 调用超时秒数",
    )

    # ==================== Milvus 向量数据库 ====================
    milvus_host: str = Field(default="localhost", description="Milvus 主机")
    milvus_port: int = Field(default=19530, description="Milvus 端口")
    milvus_collection: str = Field(default="multi_agent_kb", description="Collection 名")
    milvus_timeout_ms: int = Field(default=10000, description="连接超时 (毫秒)")
    milvus_hnsw_search_ef: int = Field(
        default=128,
        description=(
            "HNSW 查询时 ef 参数, 必须大于等于实际搜索 top-k. "
            "只影响查询召回/延迟, 不需要重建索引."
        ),
    )

    # ==================== RAG 基础 ====================
    # Parent-Child 切分: rag_chunk_size 是 child 块大小 (embedding 用, 小=召回准);
    # rag_parent_max_chars 是 parent 块上限 (拼 LLM context 用, 大=上下文全)。
    # 命中 child 后 retrieval 按 parent_id 去重并返回 parent_content。
    rag_top_k: int = Field(default=3, description="最终送给 LLM 的 top-k parent 文档数")
    rag_chunk_size: int = Field(default=300, description="Child 块大小 (字符, embedding 用; 小块召回更准)")
    rag_chunk_overlap: int = Field(default=50, description="Child 块间 overlap (字符)")
    rag_parent_max_chars: int = Field(default=2400, description="Parent 块字符上限; 超过则二次切")
    kb_admin_token: str = Field(default="", description="知识库上传/删除管理员 Token")

    # ==================== RAG Chat 会话记忆 ====================
    redis_url: str = Field(default="redis://localhost:6379/0", description="Redis 连接地址")

    # ==================== Incident Pipeline ====================
    database_url: str = Field(
        default="postgresql://multi_agent:multi_agent@localhost:5432/multi_agent_aiops",
        description="Postgres 连接地址, 用于 Incident/Evidence/AgentRun 事实库",
    )
    database_pool_min_size: int = Field(default=1, description="Postgres 连接池最小连接数")
    database_pool_max_size: int = Field(default=10, description="Postgres 连接池最大连接数")
    incident_pipeline_enabled: bool = Field(
        default=True,
        description="是否启用工业化 Incident Pipeline: Webhook 入库 + Redis Stream 入队",
    )
    incident_time_bucket_sec: int = Field(
        default=300,
        description="Incident 聚合时间桶秒数, 用于没有 groupKey 时生成 correlation_key",
    )
    incident_queue_stream: str = Field(
        default="aiops:incident_tasks",
        description="Redis Streams 中的诊断任务 stream 名",
    )
    incident_queue_dlq_stream: str = Field(
        default="aiops:incident_tasks:dlq",
        description=(
            "Redis Streams 死信队列 stream 名. "
            "为什么需要: 超过最大重试次数或消息格式损坏时, 不能无限重试, "
            "也不能静默丢弃, 所以把原消息和失败原因转移到 DLQ 供人工排查."
        ),
    )
    incident_queue_consumer_group: str = Field(
        default="diagnosis-workers",
        description="Redis Streams consumer group 名",
    )
    incident_queue_priority_enabled: bool = Field(
        default=True,
        description=(
            "是否启用优先级队列 (改造文档第 4 步). 开启后任务按严重度分流到 "
            "{stream}:critical/high/normal/low 四条 Stream, Worker 按 critical→high→normal→low "
            "顺序消费, 严重告警真正插队. 关闭则回落单 Stream FIFO."
        ),
    )
    incident_queue_maxlen: int = Field(
        default=10000,
        description="Redis Streams 近似最大长度, 防止演示环境无限增长",
    )
    diagnosis_worker_consumer_name: str = Field(
        default="worker-1",
        description="Diagnosis Worker 默认 consumer 名",
    )
    diagnosis_worker_block_ms: int = Field(
        default=5000,
        description="Diagnosis Worker 读取 Redis Stream 的阻塞等待毫秒数",
    )
    diagnosis_worker_reclaim_idle_ms: int = Field(
        default=900000,
        description=(
            "Pending 消息空闲多久后允许被其他 Worker 认领, 默认 15 分钟. "
            "为什么要比单次普通诊断长: 避免长诊断还在运行时被别的 Worker 重复执行."
        ),
    )
    diagnosis_worker_reclaim_count: int = Field(
        default=5,
        description="每轮最多回收多少条 stale pending 任务, 防止一次回收太多压垮 Worker.",
    )
    diagnosis_worker_heartbeat_interval_sec: int = Field(
        default=10,
        description="Worker heartbeat 写入 Redis 的间隔秒数.",
    )
    diagnosis_worker_heartbeat_ttl_sec: int = Field(
        default=30,
        description="Worker heartbeat key 的 TTL 秒数, 过期表示该 Worker 可能已经退出.",
    )
    diagnosis_task_timeout_sec: int = Field(
        default=600,
        description="单个诊断任务最大运行秒数. 超时后进入 retry 或 DLQ, 避免任务永久占用 Worker.",
    )
    diagnosis_task_max_attempts: int = Field(
        default=3,
        description="单个诊断任务最大尝试次数",
    )
    deep_diagnosis_enabled: bool = Field(
        default=True,
        description=(
            "deep 模式是否路由到 Deep Diagnosis Graph (多 Agent 深度诊断). "
            "默认开: 8 节点已全部填实 (Metric/Log/Runbook 隔离 subagent + EvidenceReducer "
            "+ RCAJudge + Report + EvidencePlan 规则路由 + IncidentMgr/CorrelationContext + Remediation), "
            "deep 请求会真走深度图并产出含证据链/候选/处置的 Markdown 报告 (需 langgraph 栈). "
            "置 False 则回落到 fast plan-execute-replan (无 langgraph 栈或想退回单链路时用)."
        ),
    )

    # ==================== LLM Wiki (Karpathy 模式, 取代 M10 自反思) ====================
    # 诊断收尾 ingest -> LLM 合并相关 markdown 页 (data/wiki/); 诊断前读 index 优先召回。
    # 无独立 worker / 无 Redis 流 / 无向量库。见 data/wiki/CONVENTIONS.md。
    wiki_enabled: bool = Field(
        default=True,
        description="是否在诊断收尾把本次诊断 ingest 进 LLM Wiki (data/wiki/)。关掉只是不沉淀, 不影响诊断。",
    )
    wiki_recall_enabled: bool = Field(
        default=True,
        description="是否在诊断前读 index 召回相关 wiki 页注入 prompt。召回失败永不影响诊断。",
    )
    wiki_summary_model: str = Field(
        default="",
        description="ingest 时合并页面用的模型。留空走 dashscope_router_model (便宜快); 非关键路径。",
    )
    wiki_recall_max_chars: int = Field(
        default=2000,
        description="单次召回注入的 wiki 页内容字符上限, 控制 prompt 体积。",
    )

    rag_chat_memory_enabled: bool = Field(default=False, description="是否启用 RAG Chat Redis 会话记忆")
    rag_chat_history_turns: int = Field(default=3, description="回答时注入最近 N 轮对话")
    rag_chat_memory_ttl_sec: int = Field(default=604800, description="RAG Chat 会话记忆 TTL 秒数")
    rag_chat_rewrite_enabled: bool = Field(default=True, description="是否启用多轮问题改写")
    rag_chat_compact_enabled: bool = Field(default=True, description="是否启用长会话摘要压缩")
    rag_chat_max_messages: int = Field(default=12, description="超过多少条消息触发 compact")
    rag_chat_compact_keep_messages: int = Field(default=6, description="compact 后保留最近多少条原文消息")
    rag_chat_summary_max_chars: int = Field(default=1200, description="会话摘要最大字符数")
    rag_chat_max_tool_rounds: int = Field(
        default=3,
        description=(
            "RAG Chat 工具回合最大轮次. LLM 调一次工具拿数据回来再总结算 2 轮; "
            "调多组工具串行追问算更多轮. 默认 3 轮足够'看一眼系统再回答'的场景."
        ),
    )
    rag_chat_web_search_enabled: bool = Field(default=False, description="是否允许 RAG Chat 使用受限联网搜索")
    rag_chat_web_search_max_results: int = Field(default=3, description="RAG Chat 联网搜索最大结果数")
    rag_chat_web_search_keywords: str = Field(
        default=(
            "redis,mysql,postgresql,mongodb,elasticsearch,kafka,rocketmq,rabbitmq,"
            "nginx,linux,docker,kubernetes,k8s,prometheus,grafana,jvm,java,python,"
            "go,nodejs,fastapi,langchain,langgraph,milvus,etcd,minio"
        ),
        description="RAG Chat 允许触发联网搜索的技术主题词, 英文逗号分隔",
    )

    # ==================== RAG 高级检索 (Hybrid Search + Reranker) ====================
    # 设计思路: 业界主流 "先 Hybrid 提 recall, 再 Reranker 提 precision" (Anthropic
    # Contextual Retrieval / bswen 2026 实测). 任一组件故障都会自动降级到纯向量,
    # 不影响基础功能. 全部默认开启, 通过 .env 关闭便于 A/B 对比.
    rag_retrieve_k: int = Field(
        default=20,
        description=(
            "送进 Reranker 前的候选数 (BM25 + Vector 各取这么多). "
            "为什么 20: Anthropic 实验显示 top-20 是准确率与延迟的平衡点; "
            "局限: 数值越大 rerank 延迟越高, 数值越小 reranker 发挥空间越小."
        ),
    )
    rag_hybrid_enabled: bool = Field(
        default=True,
        description=(
            "是否启用 Hybrid Search (BM25 + Vector + RRF 融合). "
            "为什么: 纯向量漏精确关键词 (服务名/错误码/数字), BM25 正好互补; "
            "局限: BM25 索引是进程内存, 多副本部署需各自构建, 新上传文档需手动或定时刷新."
        ),
    )
    rag_hybrid_bm25_weight: float = Field(
        default=0.4,
        description=(
            "Hybrid 融合中 BM25 的权重 (Vector 权重 = 1 - 该值). "
            "为什么 0.4: 语义占主导, 关键词作补充; 局限: 最优权重依赖语料, 需用 eval 脚本调优."
        ),
    )
    rag_hybrid_rrf_k: int = Field(
        default=60,
        description=(
            "RRF 融合常数. 值越小越偏向各路检索的头部结果, 值越大融合更平滑; "
            "经典默认值是 60, 但小知识库可用评测脚本调参."
        ),
    )
    rag_rerank_enabled: bool = Field(
        default=True,
        description=(
            "是否启用 Reranker. "
            "为什么: 向量相似度 ≠ 问答相关性, reranker 是 cross-encoder 能精细打分; "
            "局限: 每次查询多一次 API 调用 (约 100-300ms), 网络故障时会自动降级."
        ),
    )
    rag_rerank_provider: str = Field(
        default="dashscope",
        description="Rerank 提供方: dashscope / local. local 默认使用 FlagEmbedding.",
    )
    rag_local_rerank_backend: str = Field(
        default="flagembedding",
        description="本地 rerank 后端. 当前支持 flagembedding.",
    )
    rag_rerank_model: str = Field(
        default="gte-rerank-v2",
        description=(
            "Rerank 模型名. dashscope 推荐 gte-rerank-v2; "
            "local 推荐 BAAI/bge-reranker-v2-m3 或 Alibaba-NLP/gte-multilingual-reranker-base."
        ),
    )
    rag_local_rerank_device: str = Field(
        default="auto",
        description="本地 reranker 设备: auto / mps / cuda / cpu.",
    )
    rag_local_rerank_max_length: int = Field(
        default=512,
        description="本地 reranker 最大 token 长度. M1 上建议 512, 更大更慢.",
    )
    rag_local_rerank_batch_size: int = Field(
        default=8,
        description="本地 FlagEmbedding rerank batch size. M1 建议 4-8.",
    )
    rag_rerank_timeout_sec: float = Field(
        default=8.0,
        description="Rerank API 超时秒数. 超时即降级到纯向量结果, 不阻塞用户."
    )
    rag_rerank_use_parent_context: bool = Field(
        default=True,
        description=(
            "rerank 时是否把 parent_content 与章节信息一起送入模型. "
            "Parent-Child RAG 中 child 负责召回, reranker 看 parent 可获得更完整排障上下文."
        ),
    )
    rag_rerank_parent_max_chars: int = Field(
        default=1200,
        description="rerank 输入中 parent_content 最大字符数, 防止候选过长导致延迟和费用过高.",
    )
    rag_bm25_refresh_on_upload: bool = Field(
        default=True,
        description=(
            "文档上传后是否立即重建 BM25 索引. "
            "为什么开: 小规模知识库重建毫秒级, 体验好; "
            "局限: 知识库很大 (10 万 chunks+) 时应改为定时刷新."
        ),
    )

    # ==================== MCP 远程工具 ====================
    # 本机诊断 MCP (都是真实数据源)
    mcp_system_transport: str = Field(default="streamable-http", description="本机系统 MCP 传输")
    mcp_system_url: str = Field(default="http://localhost:8005/mcp", description="本机系统 MCP URL (psutil)")
    mcp_websearch_transport: str = Field(default="streamable-http", description="联网搜索 MCP 传输")
    mcp_websearch_url: str = Field(default="http://localhost:8006/mcp", description="联网搜索 MCP URL")
    mcp_winlog_transport: str = Field(default="streamable-http", description="Windows 事件日志 MCP 传输")
    mcp_winlog_url: str = Field(default="http://localhost:8008/mcp", description="Windows 事件日志 MCP URL")
    mcp_network_transport: str = Field(default="streamable-http", description="网络诊断 MCP 传输")
    mcp_network_url: str = Field(default="http://localhost:8009/mcp", description="网络诊断 MCP URL")
    mcp_docker_transport: str = Field(default="streamable-http", description="Docker 管理 MCP 传输")
    mcp_docker_url: str = Field(default="http://localhost:8011/mcp", description="Docker 管理 MCP URL")

    # ==================== Agent ====================
    agent_max_steps: int = Field(default=5, description="Plan-Execute 最大步骤 (防死循环)")
    agent_max_reroutes: int = Field(
        default=1,
        description=(
            "Replanner 触发 Skill reroute 的最大次数 (防 Skill 之间反复横跳). "
            "业界主流 (LangGraph Supervisor + Handoff) 通常设 1-2."
        ),
    )
    agent_reroute_min_past_steps: int = Field(
        default=2,
        description=(
            "允许触发 Skill reroute 的最小已执行步数. "
            "证据不足时 (past_steps < 该值) 即使 LLM 想切也会被阻止."
        ),
    )
    agent_max_concurrency: int = Field(default=2, description="AIOps Agent 最大并发诊断数")
    guardrails_block_high_risk_tools: bool = Field(
        default=True,
        description="是否默认拦截高风险写操作工具",
    )
    guardrails_allow_notification_tools: bool = Field(
        default=True,
        description="是否允许通知类工具",
    )
    mcp_lazy_tools_enabled: bool = Field(
        default=False,
        description=(
            "是否启用 MCP Lazy Tools 两阶段发现/执行. "
            "默认关闭: MCP 工具直接 bind 给 LLM, 单轮即可调用, 减少额外 LLM round. "
            "仅在 MCP 工具数量很大、需要按需暴露时才开启."
        ),
    )
    permission_mode: str = Field(
        default="normal",
        description=(
            "§1 cc-haha 借鉴, 工具权限模式. 取值: "
            "read_only (只允许只读工具) / normal (默认, Skill 白名单+高危黑名单) / "
            "ask_destructive (写工具走人工审批) / bypass (dev only, 跳过非硬墙检查). "
            "可被 state.permission_mode 单次会话覆盖."
        ),
    )
    approvals_enabled: bool = Field(
        default=True,
        description=(
            "是否启用真审批闭环 (ASK_DESTRUCTIVE 模式下命中 ask 时写入 approval_requests "
            "并等待人工 allow/deny). 关掉则保持旧行为: ask 直接转 deny + 提示."
        ),
    )
    approvals_timeout_sec: int = Field(
        default=300,
        description="单条审批请求最长等待秒数, 超时自动 deny.",
    )
    approvals_poll_interval_sec: float = Field(
        default=2.0,
        description="tool_runner 轮询审批决策的间隔, 越小响应越快越费 Postgres.",
    )
    skills_external_dirs: str = Field(
        default="",
        description=(
            "额外 Skill 根目录, 多个路径用逗号或系统 path separator 分隔. "
            "兼容 Hermes 风格的 <category>/<skill>/SKILL.md."
        ),
    )
    skills_disabled: str = Field(
        default="",
        description="禁用的 Skill name 列表, 多个用逗号分隔",
    )
    skills_platform: str = Field(
        default="",
        description="Skill 平台过滤值, 为空则自动识别 windows/linux/macos",
    )
    executor_parallel_enabled: bool = Field(
        default=True,
        description=(
            "Executor 是否启用 read-only 工具并行编排 (§3 cc-haha 借鉴). "
            "True 走 run_parallel_agent (按 ToolMeta.concurrency_safe 切批 gather), "
            "False 回退 langchain.agents.create_agent (默认串行, 用于排错对比)."
        ),
    )
    executor_max_iters: int = Field(
        default=4,
        description="Executor 单步内 LLM <-> tool 往返上限 (防 LLM 死循环调用工具)",
    )
    executor_max_parallel: int = Field(
        default=6,
        description="Executor 单批工具并行上限 (cc-haha 默认 10, OnCall 保守取 6)",
    )
    agent_executor_model: str = Field(
        default="",
        description=(
            "Executor 使用的模型. 留空则走 dashscope_chat_model. "
            "建议接 deepseek-v4-flash 之类的快模型: Executor 每步都要 LLM, 跑得最频繁, "
            "用 pro 会非常慢. 报告综合那一步用 pro 最划算."
        ),
    )
    agent_report_model: str = Field(
        default="",
        description=(
            "最终报告合成使用的模型. 留空则走 dashscope_chat_model (推荐 pro). "
            "Replanner 用 flash 做快速决策, 决策 is_finished=true 后再用 report_model "
            "单独写一份高质量的 5 段 SRE 报告, 质量 / 速度两头兼顾."
        ),
    )
    agent_planner_model: str = Field(
        default="",
        description=(
            "Planner / Replanner 使用的模型. 留空则走 dashscope_router_model (qwen-turbo). "
            "结构化输出 (Plan/Act) 不需要大模型, 用 router_model 可减少 60-80% 时延. "
            "想换回 qwen-max 填 'qwen-max' 即可."
        ),
    )
    agent_replanner_fast_path_threshold: int = Field(
        default=2,
        description=(
            "Replanner 快路径门槛: 当 plan 剩余步数 >= 该值且上一步未失败时, "
            "跳过 Replanner LLM 直接进入下一步. 设为 0 则禁用快路径 (每步都 replan)."
        ),
    )
    agent_replanner_past_step_chars: int = Field(
        default=2000,
        description=(
            "Replanner prompt 中每条 past_step result 的字符上限. "
            "防止全量历史 (尤其工具返回 10KB+) 把 LLM 上下文撑爆, 也提速."
        ),
    )
    harness_max_total_tokens: int = Field(default=0, description="单次 Harness run 的总 token 硬上限, 0 表示不限制")
    harness_max_total_ms: int = Field(default=0, description="单次 Harness run 的总耗时硬上限, 0 表示不限制")
    harness_budget_warn_ratio: float = Field(default=0.8, description="达到预算比例后输出 warning 事件")

    # ==================== 限流 (用户/IP/来源) ====================
    rate_limit_enabled: bool = Field(
        default=True,
        description="是否启用接口限流 (改造文档第 8 步). Redis 不可用时自动放行 (fail-open).",
    )
    rate_limit_manual_per_ip_per_min: int = Field(
        default=20,
        description="单 IP 每分钟最多手动诊断请求数 (同步 diagnose + submit 共用)",
    )
    rate_limit_webhook_per_source_per_min: int = Field(
        default=500,
        description="单来源 (Alertmanager receiver) 每分钟最多告警条数",
    )
    rate_limit_webhook_per_ip_per_sec: int = Field(
        default=50,
        description="单 IP/API Key 每秒最多 webhook 请求数",
    )

    # ==================== 高并发 / 分布式限流 ====================
    # 把进程内 asyncio.Semaphore 升级为 Redis 全局并发槽, 多 uvicorn worker 共享上限.
    distributed_limiter_enabled: bool = Field(
        default=True,
        description="是否启用 Redis 分布式并发槽 (跨进程全局限流). 关掉则各入口不限流 (仅本地开发).",
    )
    limiter_key_prefix: str = Field(
        default="aiops:limiter",
        description="分布式并发槽在 Redis 里的 key 前缀, 形如 aiops:limiter:{resource}",
    )
    limiter_default_ttl_sec: int = Field(
        default=90,
        description="槽位 TTL 秒数: 进程崩溃没释放时, 到期自动回收, 防止槽位永久泄漏",
    )
    limiter_default_refresh_sec: int = Field(
        default=30,
        description="长任务运行期间心跳续期间隔, 必须明显小于 TTL",
    )
    manual_diagnosis_concurrency: int = Field(
        default=2,
        description="手动诊断 (同步 SSE 入口) 全局并发上限. 满了同步入口返回'稍后重试'或走 submit 排队.",
    )
    worker_diagnosis_concurrency: int = Field(
        default=2,
        description="后台 Worker 诊断全局并发上限 (所有 Worker 副本共享). 满了 Worker 等待而不是超跑.",
    )

    # ==================== Prometheus / 真指标后端 (可选) ====================
    # 留空 = 未启用, MetricAgent / 任何 Skill 仍可调本机 system 工具兜底.
    # 配上 URL 后 MetricAgent 优先尝试 PromQL, 失败/超时再降级本机.
    prometheus_url: str = Field(
        default="",
        description="Prometheus / VictoriaMetrics HTTP API 基地址, 留空则禁用真指标后端",
    )
    prometheus_timeout_sec: float = Field(
        default=8.0,
        description="Prometheus HTTP API 超时秒数, 超时即返回错误说明, 不阻塞诊断主链路",
    )

    # ==================== 联网搜索 ====================
    # provider 可选: open_websearch (本地 daemon, 无 API Key) / mock / ddgs (国内不稳)
    web_search_provider: str = Field(
        default="open_websearch",
        description="联网搜索 provider: open_websearch / mock / ddgs",
    )
    open_websearch_base_url: str = Field(
        default="http://127.0.0.1:3210",
        description="open-webSearch 本地 daemon 地址",
    )
    open_websearch_engine: str = Field(
        default="bing",
        description="open-webSearch 默认搜索引擎, 如 bing / baidu / duckduckgo / startpage",
    )
    open_websearch_search_mode: str = Field(
        default="auto",
        description="open-webSearch 搜索模式: request / auto / playwright",
    )
    open_websearch_timeout_sec: float = Field(
        default=15.0,
        description="open-webSearch HTTP 调用超时秒数",
    )


    # ==================== 本地 LLM 兜底 (断网/无 API key 时使用) ====================
    local_llm_enabled: bool = Field(
        default=False,
        description="是否启用本地 LLM 兜底 (DashScope 不可达时自动切换)",
    )
    local_llm_force: bool = Field(
        default=False,
        description="强制使用本地 LLM (跳过 DashScope), 适合无 API key 或纯离线开发",
    )
    local_llm_base_url: str = Field(
        default="http://localhost:11434/v1",
        description="本地 LLM OpenAI 兼容接口 URL (Ollama 默认 11434)",
    )
    local_llm_model: str = Field(
        default="qwen2.5:7b",
        description="本地 LLM 模型名 (建议 qwen2.5:7b 或更大, 需支持 tool calling)",
    )
    local_llm_api_key: str = Field(
        default="ollama",
        description="本地 LLM API Key (Ollama 任意值即可, 一般填 'ollama')",
    )
    local_llm_probe_host: str = Field(
        default="dashscope.aliyuncs.com",
        description="探测 DashScope 是否可达的目标域名 (TCP 443)",
    )
    local_llm_probe_ttl_sec: int = Field(
        default=30,
        description="探测结果缓存秒数 (防止每次调用都探测)",
    )

    # ==================== 日志 ====================
    log_level: str = Field(default="INFO", description="日志级别")
    log_dir: str = Field(default="logs", description="日志目录")
    log_retention_days: int = Field(default=14, description="日志保留天数")

    # ==================== 计算属性 ====================
    @property
    def mcp_servers(self) -> Dict[str, Dict[str, Any]]:
        """组装 MCP 服务器配置.

        将扁平字段转为 langchain-mcp-adapters 期望的嵌套字典.
        新增 MCP 服务时, 在此添加映射.
        """
        return {
            "system": {
                "transport": self.mcp_system_transport,
                "url": self.mcp_system_url,
            },
            "websearch": {
                "transport": self.mcp_websearch_transport,
                "url": self.mcp_websearch_url,
            },
            "winlog": {
                "transport": self.mcp_winlog_transport,
                "url": self.mcp_winlog_url,
            },
            "network": {
                "transport": self.mcp_network_transport,
                "url": self.mcp_network_url,
            },
            "docker": {
                "transport": self.mcp_docker_transport,
                "url": self.mcp_docker_url,
            },
        }

    # ==================== 校验 ====================
    @field_validator("dashscope_api_key")
    @classmethod
    def _validate_api_key(cls, v: str) -> str:
        if not v or v.startswith("sk-your") or v == "":
            # 不直接 raise, 启动时由 main.py 统一检查并给出友好提示
            return v
        return v

    @field_validator("log_level")
    @classmethod
    def _normalize_log_level(cls, v: str) -> str:
        return v.upper()

    @field_validator("embedding_provider")
    @classmethod
    def _normalize_embedding_provider(cls, v: str) -> str:
        value = (v or "dashscope").lower().strip()
        if value not in {"dashscope", "ollama"}:
            raise ValueError("embedding_provider 只能是 dashscope 或 ollama")
        return value

    def validate_runtime(self) -> None:
        """运行时校验 (启动时调用).

        与 Pydantic 字段校验不同, 这里检查的是运行所需的实际值.
        """
        configured_models = [
            self.dashscope_chat_model,
            self.dashscope_router_model,
            self.agent_planner_model,
            self.agent_executor_model,
            self.agent_report_model,
        ]
        uses_dashscope = any(
            (model or "").strip()
            and not (model or "").strip().lower().startswith("deepseek")
            for model in configured_models
        )
        uses_deepseek = any(
            (model or "").strip().lower().startswith("deepseek")
            for model in configured_models
        )

        if uses_dashscope and (
            not self.dashscope_api_key or self.dashscope_api_key.startswith("sk-your")
        ):
            raise RuntimeError(
                "DASHSCOPE_API_KEY 未配置. 请编辑 .env 文件填入真实 API key. "
                "申请地址: https://bailian.console.aliyun.com/"
            )
        if uses_deepseek and (
            not self.deepseek_api_key or self.deepseek_api_key.startswith("sk-your")
        ):
            raise RuntimeError(
                "DEEPSEEK_API_KEY 未配置. 当前模型配置使用 deepseek*, "
                "请编辑 .env 文件填入真实 DeepSeek API key. "
                "申请地址: https://platform.deepseek.com/"
            )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """获取配置单例.

    使用 lru_cache 保证整个进程只创建一次.
    便于测试时通过 get_settings.cache_clear() 重置.
    """
    return Settings()


# 全局便捷访问
settings = get_settings()
