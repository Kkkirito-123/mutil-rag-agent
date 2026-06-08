# Ragas RAG 评测报告

样本数: **3**

## 平均得分

| 指标 | 平均分 | 含义 |
|---|---|---|
| faithfulness | 0.333 | 答案是否忠于检索上下文 (无编造) |
| answer_relevancy | 0.899 | 答案是否切题 |
| context_precision | 1.000 | 检索排序是否准 (相关在前) |
| context_recall | 0.767 | 检索是否覆盖 ground_truth (无遗漏) |

## 逐条结果

### Q1: Redis 连接池耗尽导致 5xx 升高,怎么排查?

- **ground_truth**: 查看 connected_clients 与 maxclients 比例; 找住连接不释放的客户端 (CLIENT LIST 看 idle); 排查应用侧连接泄漏 (未关闭 / 长事务); 临时扩 maxclients 缓解。
- **生成回答**: 根据上下文，排查 Redis 连接池耗尽导致 5xx 升高，建议按以下步骤进行：

1.  **检查 Redis 服务端连接数**：执行 `redis-cli INFO clients` 和 `CONFIG GET maxclients`，重点看 `connected_clients` 是否接近上限。
2.  **定位异常客户端**：执行 `redis-cli CLIENT LIST`，关注 `idle` 值很高的连接，这通常意味着应用侧未释放连接。
3.  **排查应用侧连接池**：检查连接池配置（如 Jedis/Lettuce），确认是否有连接泄漏（如未在 finally 中 close）、长事务或阻塞命令。
4.  **关联分析**：结合 `SLOWLOG GET 20` 查看慢日志，并遵循 RAIL 法则，检查近期是否有变更、相关依赖告警或日志中的 `Could not get a resource from the pool` 等堆栈。
- **得分**: faithfulness=0.182 | answer_relevancy=0.977 | context_precision=1.000 | context_recall=0.500

### Q2: MySQL 慢查询拖垮接口,常见原因和处置?

- **ground_truth**: 看 slow_query_log + EXPLAIN 找无索引或全表扫; 看 SHOW PROCESSLIST 是否有锁等待; innodb_buffer_pool_size 是否过小; 索引缺失加索引,锁等待杀长事务。
- **生成回答**: 常见原因：SQL 未命中索引或全表扫描；大事务或锁等待阻塞；`innodb_buffer_pool_size` 不足导致大量磁盘 IO；以及 `rows_examined` 远大于 `rows_sent` 的低效查询。  
处置：紧急时 KILL 异常长事务或回滚发布；长期需为慢查询添加合适联合索引、拆分大事务、调整缓冲池大小，必要时限流或读写分离。
- **得分**: faithfulness=0.000 | answer_relevancy=0.887 | context_precision=1.000 | context_recall=0.800

### Q3: Kubernetes Pod 反复 CrashLoopBackOff 怎么定位?

- **ground_truth**: kubectl describe pod 看 Last State 与 Reason; kubectl logs --previous 看上一次崩溃日志; 常见: OOMKilled 调 limits.memory、配置错误改 env/configmap、就绪探针失败查健康检查。
- **生成回答**: 定位 CrashLoopBackOff 主要分三步：  
1. 用 `kubectl describe pod` 查看 `Last State`、`Exit Code` 和 Events，判断退出原因（如 OOMKilled 或探针失败）。  
2. 用 `kubectl logs <pod> --previous` 抓取上一次容器的日志，检查应用启动报错或依赖连接失败。  
3. 结合常见根因排查：OOM 则看内存限制，探针失败则检查 liveness 配置，配置错误则核对 ConfigMap/Secret，依赖不可用则确认下游服务。
- **得分**: faithfulness=0.818 | answer_relevancy=0.833 | context_precision=1.000 | context_recall=1.000
