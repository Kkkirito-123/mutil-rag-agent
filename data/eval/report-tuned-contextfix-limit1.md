# Ragas RAG 评测报告

样本数: **1**

## 平均得分

| 指标 | 平均分 | 含义 |
|---|---|---|
| faithfulness | 1.000 | 答案是否忠于检索上下文 (无编造) |
| answer_relevancy | 0.977 | 答案是否切题 |
| context_precision | 1.000 | 检索排序是否准 (相关在前) |
| context_recall | 1.000 | 检索是否覆盖 ground_truth (无遗漏) |

## 逐条结果

### Q1: Redis 连接池耗尽导致 5xx 升高,怎么排查?

- **ground_truth**: 查看 connected_clients 与 maxclients 比例; 找住连接不释放的客户端 (CLIENT LIST 看 idle); 排查应用侧连接泄漏 (未关闭 / 长事务); 临时扩 maxclients 缓解。
- **生成回答**: 根据上下文，排查 Redis 连接池耗尽导致 5xx 升高，建议按以下步骤进行：

1.  **检查 Redis 服务端连接数**：执行 `redis-cli INFO clients` 和 `CONFIG GET maxclients`，重点看 `connected_clients` 是否接近 `maxclients` 上限。
2.  **定位异常客户端**：执行 `redis-cli CLIENT LIST`，关注 `idle` 时间很长的连接，这通常意味着应用侧未正确释放连接。
3.  **排查应用侧连接池**：检查应用（如 Jedis/Lettuce）的连接池配置，确认 `active` 连接数是否长时间接近 `maxActive`，并检查代码中是否有连接未在 `finally` 块中关闭的泄漏问题。
4.  **关联慢日志与 CPU**：执行 `redis-cli SLOWLOG GET 20` 查看是否有慢查询导致连接被长时间占用。
- **得分**: faithfulness=1.000 | answer_relevancy=0.977 | context_precision=1.000 | context_recall=1.000
