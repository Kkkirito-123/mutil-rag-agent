# Ragas RAG 评测报告

样本数: **1**

## 平均得分

| 指标 | 平均分 | 含义 |
|---|---|---|
| faithfulness | 0.125 | 答案是否忠于检索上下文 (无编造) |
| answer_relevancy | nan | 答案是否切题 |
| context_precision | 0.000 | 检索排序是否准 (相关在前) |
| context_recall | 0.000 | 检索是否覆盖 ground_truth (无遗漏) |

## 逐条结果

### Q1: Redis 连接池耗尽导致 5xx 升高,怎么排查?

- **ground_truth**: 查看 connected_clients 与 maxclients 比例; 找住连接不释放的客户端 (CLIENT LIST 看 idle); 排查应用侧连接泄漏 (未关闭 / 长事务); 临时扩 maxclients 缓解。
- **生成回答**: 根据你的描述，我无法从提供的上下文中找到具体信息。但基于通用排查思路，建议你：先检查应用侧连接池配置（如最大连接数、超时时间）是否过小；再通过 `redis-cli INFO clients` 查看 Redis 实例的当前连接数是否接近上限；同时检查业务侧是否有慢查询或未释放的连接导致泄漏。
- **得分**: faithfulness=0.125 | answer_relevancy=nan | context_precision=0.000 | context_recall=0.000
