# Ragas RAG 评测报告

样本数: **1**

## 平均得分

| 指标 | 平均分 | 含义 |
|---|---|---|
| faithfulness | 0.208 | 答案是否忠于检索上下文 (无编造) |
| answer_relevancy | 0.868 | 答案是否切题 |
| context_precision | 0.333 | 检索排序是否准 (相关在前) |
| context_recall | 0.000 | 检索是否覆盖 ground_truth (无遗漏) |

## 逐条结果

### Q1: Redis 连接池耗尽导致 5xx 升高,怎么排查?

- **ground_truth**: 查看 connected_clients 与 maxclients 比例; 找住连接不释放的客户端 (CLIENT LIST 看 idle); 排查应用侧连接泄漏 (未关闭 / 长事务); 临时扩 maxclients 缓解。
- **生成回答**: 根据上下文，排查思路如下：

1. **先按 RAIL 法则排查近期变更**：检查是否有新版本上线、配置变更或突发流量，这些可能导致连接池需求激增。
2. **关联 Redis 告警**：查看同时段是否有 Redis 内存使用率过高（OOM）或碎片率过高的告警，这些会导致连接阻塞或断开，从而耗尽连接池。
3. **检查 Redis 侧连接数**：在 Redis 实例上执行 `INFO clients`，查看 `connected_clients` 是否接近 `maxclients` 限制，确认是否因连接数打满导致拒绝新连接。
4. **分析日志定位根因**：从 5xx 请求中抽样 traceId，在全链路日志中查找 Redis 相关的超时或连接拒绝错误，确认是客户端池配置不足还是 Redis 服务端问题。
- **得分**: faithfulness=0.208 | answer_relevancy=0.868 | context_precision=0.333 | context_recall=0.000
