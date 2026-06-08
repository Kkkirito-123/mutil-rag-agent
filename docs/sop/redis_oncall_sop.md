# Redis On-Call SOP

> 适用范围: 生产环境 Redis 集群 (主从 / Cluster 模式) 故障处理标准流程

## 第一章 内存类问题

### 1.1 内存使用率过高 (used_memory > 90% maxmemory)

#### 现象
- 客户端报错 `OOM command not allowed when used memory > 'maxmemory'`
- 写操作失败, 读操作可能正常
- 连接被强制断开

#### 排查步骤
1. **确认实际内存占用**
   ```bash
   redis-cli INFO memory
   # 关注: used_memory, used_memory_peak, maxmemory, mem_fragmentation_ratio
   ```

2. **定位大 Key (绝不要在生产用 KEYS 命令!)**
   ```bash
   # 用 SCAN 替代 KEYS, 不阻塞主线程
   redis-cli --bigkeys
   # 或者用 SCAN + MEMORY USAGE
   redis-cli SCAN 0 COUNT 100
   ```

3. **检查淘汰策略**
   ```bash
   redis-cli CONFIG GET maxmemory-policy
   # 推荐: allkeys-lru (一般业务) / volatile-lru (设置了 TTL)
   ```

4. **查看键过期分布**
   - 如果大量 key 没设 TTL → 业务侧要补
   - `redis-cli INFO keyspace` 看 keys / expires 比例

#### 处置方案

##### 紧急止损 (5 分钟内)
1. 临时上调 maxmemory (前提是宿主机内存够)
   ```bash
   redis-cli CONFIG SET maxmemory 8gb
   ```
2. 删除明确无用的大 key (例如废弃业务的缓存)
   ```bash
   redis-cli DEL <大 key 名字>
   # 或异步删除避免阻塞
   redis-cli UNLINK <大 key 名字>
   ```
3. 临时调整淘汰策略为 `allkeys-lru` 让 Redis 自动腾空间

##### 长期优化
1. 业务方审查写入逻辑, 给所有 key 设 TTL
2. 大 key 拆分: 例如把一个百万元素的 ZSET 按 hash 分到 100 个小 ZSET
3. 监控告警: 在 80% 阈值就告警, 不等 95%

### 1.2 内存碎片率过高 (mem_fragmentation_ratio > 1.5)

#### 现象
- INFO memory 看到 mem_fragmentation_ratio > 1.5
- used_memory_rss 远大于 used_memory

#### 处置
- Redis 4.0+ 开启自动 defrag:
  ```bash
  redis-cli CONFIG SET activedefrag yes
  ```
- 或低峰期重启实例 (有副本时滚动重启)

## 第二章 性能类问题

### 2.1 CPU 100%

#### 排查
1. 用 `redis-cli --latency` 看延迟
2. `SLOWLOG GET 20` 拉慢日志
3. `CLIENT LIST` 看是否有异常连接 / pipeline 风暴

#### 常见原因
- KEYS 等阻塞命令被业务调用
- 大 key 的 SMEMBERS / HGETALL 等全量操作
- 持久化 (BGSAVE) 与高 QPS 叠加
- Lua 脚本执行时间过长

#### 处置
- 立即定位发起方 (CLIENT LIST 看 IP 端口)
- 联系业务方紧急停止
- 长期: 接入慢日志告警, 设 CPU 阈值告警
