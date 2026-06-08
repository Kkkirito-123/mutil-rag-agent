# MySQL On-Call SOP

> 适用范围: 生产环境 MySQL 主从 / 集群

## 第一章 性能类问题

### 1.1 CPU 持续 100%

#### 现象
- 业务侧大量超时
- show processlist 看到大量 Running 状态查询

#### 排查步骤

1. **查看活跃会话**
   ```sql
   SHOW FULL PROCESSLIST;
   -- 关注 Time 长 + State='Sending data'/'Copying to tmp table' 的会话
   ```

2. **看慢查询日志**
   ```bash
   tail -1000 /var/log/mysql/slow.log | grep -A 5 "Query_time:"
   ```
   关注 `rows_examined` 远大于 `rows_sent` 的查询。

3. **定位 Top SQL**
   ```sql
   SELECT digest_text, count_star, avg_timer_wait/1e9 as avg_ms
     FROM performance_schema.events_statements_summary_by_digest
     ORDER BY sum_timer_wait DESC LIMIT 10;
   ```

4. **看锁等待**
   ```sql
   SELECT * FROM information_schema.innodb_trx
     WHERE trx_state='LOCK WAIT';
   ```

#### 处置

##### 紧急
1. KILL 异常长事务
   ```sql
   KILL 12345;
   ```
2. 如果是某条 SQL 拖垮全库, 临时加 hint 或回滚发布

##### 长期
- 给慢查询加索引
- 大表分库分表
- 业务高峰前做 EXPLAIN 自检

### 1.2 主从复制延迟 (Seconds_Behind_Master 持续增长)

#### 排查
```sql
SHOW SLAVE STATUS\G
-- 关注 Seconds_Behind_Master, Slave_IO_Running, Slave_SQL_Running
```

#### 常见原因
- 主库 DDL 大事务
- 从库硬件性能不足
- 单线程回放跟不上多线程写入

#### 处置
- 开启并行复制 (slave_parallel_workers)
- 大事务拆分小事务
- 业务侧可承受时, 重新搭建从库

## 第二章 连接类问题

### 2.1 连接数打满 (Too many connections)

#### 排查
```sql
SHOW VARIABLES LIKE 'max_connections';
SHOW STATUS LIKE 'Threads_connected';
SELECT user, count(*) FROM information_schema.processlist GROUP BY user;
```

#### 处置
- 紧急: SET GLOBAL max_connections=1000
- 长期: 业务侧加连接池, 控制单实例连接数
