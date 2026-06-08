# OnCall Eval Runbooks

> 适用范围: RAGAS 评测题集覆盖的常见中间件、系统和链路告警。每个章节给出可直接用于一线排查的最小 runbook。

## Redis 故障

### Redis 连接池耗尽导致 5xx 升高

#### 现象
- 应用侧 5xx、Redis timeout、`Could not get a resource from the pool`、`ERR max number of clients reached` 增多。
- Redis 服务端 `connected_clients` 接近 `maxclients`，或应用连接池 active 长时间接近 maxActive。

#### 排查步骤
1. 看 Redis 服务端连接数。
   ```bash
   redis-cli INFO clients
   redis-cli CONFIG GET maxclients
   ```
   重点比较 `connected_clients` 与 `maxclients`，同时关注 `blocked_clients`。
2. 找连接不释放的客户端。
   ```bash
   redis-cli CLIENT LIST
   ```
   关注 `addr`、`name`、`age`、`idle`、`cmd`。大量 `idle` 很高的连接通常说明应用侧未释放连接或连接池配置过大。
3. 排查应用侧连接池。
   - Java 常见检查 Jedis/Lettuce/Hikari 配置，确认 borrow 后是否 finally close。
   - 看连接池指标: active、idle、waiters、borrow latency。
   - 检查是否有长事务、pipeline 风暴、阻塞命令导致连接长时间占用。
4. 关联 Redis 慢日志和 CPU。
   ```bash
   redis-cli SLOWLOG GET 20
   redis-cli INFO commandstats
   ```

#### 处置
- 紧急止损: 在宿主机资源允许时临时调大 `maxclients`，并同步调高文件句柄限制。
- 应用侧: 回滚异常版本，修复连接泄漏，确保连接归还；限制单实例连接池上限。
- 长期治理: 连接池 active/waiters 告警，Redis `connected_clients/maxclients` 超过 80% 预警。

### Redis CLIENT LIST idle 高连接泄漏

#### 现象
- `redis-cli CLIENT LIST` 里同一批应用地址连接数量异常多，`age` 很大且 `idle` 持续升高。
- 应用报 Redis timeout、连接池 waiters 增加，但 Redis QPS 未必同步升高。

#### 排查步骤
1. 按 `addr`、`name`、`cmd` 聚合同一应用实例的连接，确认是不是连接池未归还。
2. 对比应用连接池 active、idle、maxActive、borrow latency，看是否存在 borrow 后没有 close 的代码路径。
3. 检查 pipeline、事务、阻塞命令或慢命令是否让连接长期占用。
4. Java 客户端重点看 Jedis 是否 finally close，Lettuce 是否复用连接过度或异步 future 未消费。

#### 处置
- 先限流或重启异常应用实例释放泄漏连接。
- 将连接池上限控制在服务端 `maxclients` 可承受范围内，避免所有实例叠加后打满 Redis。
- 修复连接生命周期，增加连接池 waiters、borrow timeout、idle age 的应用侧告警。

## MySQL 故障

### MySQL 慢查询拖垮接口

#### 现象
- 接口 RT、P99、错误率上升，MySQL CPU 或 IO 飙高。
- `SHOW PROCESSLIST` 看到大量 Running、Sending data、Copying to tmp table 或 Lock wait。

#### 排查步骤
1. 打开并查看慢查询日志。
   ```sql
   SHOW VARIABLES LIKE 'slow_query_log';
   SHOW VARIABLES LIKE 'long_query_time';
   ```
   ```bash
   tail -1000 /var/log/mysql/slow.log
   ```
2. 对慢 SQL 做 EXPLAIN。
   ```sql
   EXPLAIN SELECT ...;
   ```
   重点看 `type`、`key`、`rows`、`Extra`，警惕全表扫描、未命中索引、Using filesort、Using temporary。
3. 检查锁等待和长事务。
   ```sql
   SHOW FULL PROCESSLIST;
   SELECT * FROM information_schema.innodb_trx;
   ```
4. 检查缓存和 IO。
   ```sql
   SHOW VARIABLES LIKE 'innodb_buffer_pool_size';
   SHOW GLOBAL STATUS LIKE 'Innodb_buffer_pool_read%';
   ```

#### 处置
- 缺索引: 添加合适联合索引，避免低选择性单列索引。
- 锁等待: KILL 明确异常的长事务，推动业务拆分大事务。
- 资源不足: 调整 `innodb_buffer_pool_size`，必要时限流、读写分离或回滚发布。

### MySQL Sending data 与 rows_examined 异常

#### 判断口径
- `SHOW FULL PROCESSLIST` 中长时间处于 `Sending data`，通常表示 MySQL 正在读取、过滤或发送结果，不等同于网络发送慢。
- `rows_examined` 远大于 `rows_sent`，说明扫描了大量行但只返回少量结果，应优先检查索引和执行计划。

#### 排查与处置
1. 记录长时间 `Sending data` 会话的 SQL、执行时间和线程 ID。
2. 对 SQL 执行 `EXPLAIN`，重点检查 `type`、`key`、`rows`、`Using temporary`、`Using filesort`。
3. 同时检查 `innodb_trx` 和锁等待，避免把被锁阻塞误判为单纯慢查询。
4. 明确异常 SQL 后可先限流、回滚相关发布或 KILL 异常会话，再补索引和缩小扫描范围。

## Kubernetes 故障

### Pod 反复 CrashLoopBackOff

#### 现象
- Pod 状态为 `CrashLoopBackOff`，重启次数持续增加。
- 容器短时间启动后退出，或健康检查失败被 kubelet 拉起。

#### 排查步骤
1. 查看 Pod 事件和上一次退出原因。
   ```bash
   kubectl describe pod <pod> -n <ns>
   ```
   关注 `Last State`、`Reason`、`Exit Code`、`Events`。
2. 查看上一次容器日志。
   ```bash
   kubectl logs <pod> -n <ns> --previous
   ```
3. 判断常见根因。
   - `OOMKilled`: memory limit 太小或应用内存泄漏。
   - 配置错误: ConfigMap、Secret、环境变量缺失或格式错误。
   - 探针失败: liveness 太激进，应用启动慢。
   - 依赖不可用: DB、Redis、下游服务无法连接。

#### 处置
- OOM: 调大 memory limit，抓 heap dump 或内存 profile。
- 探针: 增加 `startupProbe` 或调大 `initialDelaySeconds`。
- 配置: 修正 ConfigMap/Secret 后滚动重启。
- 依赖: 增加启动重试，readiness 未通过前不要接流量。

## Linux 主机故障

### CPU 飙到 100%

#### 排查步骤
1. 用 `top` 或 `htop` 找占用最高进程，区分 `%us`、`%sy`、`%wa`。
2. 用 `pidstat` 找线程级热点。
   ```bash
   pidstat -u -t -p <pid> 1
   ```
3. 将线程 ID 转十六进制，对 Java 进程配合 `jstack`。
   ```bash
   printf "%x\n" <tid>
   jstack <pid> | grep -A 30 nid=0x...
   ```
4. 原生进程用 `perf top`，Python 用 `py-spy top`，Go 用 pprof。

#### 处置
- 用户态 CPU 高: 定位热点函数，临时扩容或回滚异常版本。
- 内核态 CPU 高: 检查系统调用、网络包、锁竞争。
- IO wait 高: 不是纯 CPU 问题，转查磁盘或网络 IO。

### CPU us sy wa 与 load average 异常

#### 判断口径
- `%us` 高通常是用户态代码消耗 CPU，例如热点函数、死循环、序列化、正则或加解密。
- `%sy` 高通常是内核态开销，例如系统调用、网络包处理、文件 IO、锁竞争或容器网络问题。
- `%wa` 高说明 CPU 在等待 IO，常见于磁盘慢、块设备队列积压、NFS 或云盘抖动。
- load average 高但 CPU 不高时，要重点看 D 状态进程、IO wait、不可中断睡眠和线程数暴涨。

#### 排查步骤
1. 用 `top` 看 `%us/%sy/%wa` 和 load average，再按 `1` 展开多核。
2. 用 `ps -eo state,pid,ppid,comm,wchan:30 | awk '$1 ~ /D/'` 找 D 状态进程。
3. 用 `iostat -xz 1` 看 `await`、`svctm`、`util`、队列长度，判断磁盘是否拖慢。
4. 用 `pidstat -d -p ALL 1` 找产生大量读写的进程。
5. 如果 load 是线程数撑高，用 `ps -eLf | wc -l` 和 `pidstat -u -t` 定位线程来源。

#### 处置
- 用户态热点: 回滚、扩容或优化热点代码。
- 内核态异常: 检查系统调用风暴、网络连接数、iptables 或 eBPF/agent 开销。
- IO wait: 先降级大查询、批处理和日志写入，再扩容磁盘或迁移热点数据。

## Linux 内存故障

### Linux 内存告警 available buff cache 与泄漏区分

#### 判断口径
- `free -h` 中 `buff/cache` 高不一定是泄漏，Linux 会用空闲内存做页缓存。
- `available` 持续下降并接近 0，且进程 RSS、容器 working set 或 cgroup memory 持续上升，更像真实内存压力。
- `cached` 可回收但 `SUnreclaim`、slab、page table 异常升高时，要怀疑内核对象或文件系统相关问题。

#### 排查步骤
1. 看整体内存。
   ```bash
   free -h
   cat /proc/meminfo | egrep 'MemAvailable|Cached|Buffers|Slab|SUnreclaim'
   ```
2. 找进程 RSS 和增长趋势。
   ```bash
   ps aux --sort=-rss | head
   pidstat -r 1
   ```
3. 容器环境区分 limit、working set 和 OOMKilled。
   ```bash
   kubectl describe pod <pod> -n <ns>
   kubectl top pod <pod> -n <ns>
   ```
4. Java 进程同时检查 heap、Metaspace、Direct Buffer、线程栈和 native memory。

#### 处置
- 只是缓存高且 `available` 足够: 不要盲目清 cache，先降低误报阈值。
- 真实泄漏: 抓 heap dump、内存 profile 或 native memory tracking，回滚异常版本。
- 容器 OOM: 调整 limit/request，控制批量加载和本地缓存上限。

## Linux 磁盘故障

### 磁盘空间 95% 告警

#### 排查步骤
1. 定位满的挂载点。
   ```bash
   df -h
   ```
2. 只在该挂载点所在的文件系统内找大目录和大文件，避免扫描其他挂载点。`du -x`（下面与 `-h` 合并写成 `-xh`）会跳过其他文件系统，`find -xdev` 也不会进入其他文件系统。
   ```bash
   du -xh /var | sort -h | tail -20
   find / -xdev -type f -size +1G 2>/dev/null
   ```
3. 检查已删除但仍被进程占用的文件。
   ```bash
   lsof | grep deleted
   ```
4. 容器环境检查 overlay、容器日志和镜像层。
   ```bash
   docker system df
   du -sh /var/lib/docker/containers/*
   ```

#### 处置
- 先清理可确认无用的旧日志、临时文件、core dump。
- 对日志配置 logrotate，避免直接 rm 当前活跃日志。
- 对被进程持有的 deleted 文件，重启对应进程释放空间。

### deleted 文件与 core dump 占满磁盘

#### 判断与处置
- `rm` 大日志后 `df` 不下降但 `du` 已下降，通常是进程仍持有已删除文件的文件描述符。
- 用 `lsof | grep deleted` 找到进程和文件；优先让进程重新打开日志，无法安全 reopen 时再滚动重启对应实例释放空间。
- core dump 堆积时先确认文件路径、归属进程和保留要求，再清理已确认无用的旧 dump。
- 长期通过 core dump 大小/数量限制、独立目录、定期清理和磁盘告警避免再次占满。

## Nginx 故障

### 大量 502 Bad Gateway

#### 现象
- Nginx access log 出现大量 502。
- error log 常见 `connect() failed`、`upstream timed out`、`connection reset by peer`、`no live upstreams`。

#### 排查步骤
1. 直接访问 upstream，确认上游服务是否存活。
   ```bash
   curl -v http://<upstream-host>:<port>/health
   ```
2. 查看 Nginx error log。
   ```bash
   tail -200 /var/log/nginx/error.log
   ```
3. 检查超时和连接池参数。
   - `proxy_connect_timeout`
   - `proxy_read_timeout`
   - upstream keepalive
   - `worker_connections`
4. 检查上游是否重启、过载、端口耗尽或连接被提前关闭。

#### 处置
- 上游挂了: 回滚、扩容、摘除异常实例。
- 超时过短: 调整 `proxy_connect_timeout`、`proxy_read_timeout`。
- 连接不够: 调大 `worker_connections`、upstream keepalive，检查系统文件句柄。

### Nginx upstream timeout 与 worker connection 耗尽

#### 现象
- error log 出现 `upstream timed out`、`connect() failed`、`no live upstreams`。
- 大量请求卡在 upstream，`proxy_connect_timeout` 或 `proxy_read_timeout` 触发。
- `worker_connections are not enough`、`too many open files` 或 socket 耗尽。

#### 排查步骤
1. 超时类问题先直接访问 upstream health，排除上游慢、上游不可达和 DNS 解析问题。
2. 对比 `proxy_connect_timeout`、`proxy_read_timeout` 与上游真实 P99/P999，确认是不是 timeout 过短。
3. 看 worker 与文件句柄。
   ```bash
   nginx -T | egrep 'worker_processes|worker_connections|keepalive|proxy_.*timeout'
   ulimit -n
   ss -s
   ```
4. 检查 upstream keepalive 是否太小、连接复用不足，或 keepalive 太大导致空闲 socket 占满。

#### 处置
- 上游慢: 先摘除异常实例、扩容或限流，避免把 Nginx worker 拖满。
- timeout 不匹配: 调整 `proxy_connect_timeout`、`proxy_read_timeout`，并同步业务超时预算。
- 连接耗尽: 调大 `worker_connections`、系统 `nofile`、upstream keepalive，并控制客户端长连接数量。

## JVM 故障

### JVM 应用频繁 Full GC

#### 现象
- Full GC 次数持续增加，接口 RT 抖动，P99 飙升。
- GC 日志显示 Old 区回收后仍接近满。

#### 排查步骤
1. 查看 GC 频率和各区使用率。
   ```bash
   jstat -gcutil <pid> 1000 10
   ```
2. 查看对象分布。
   ```bash
   jmap -histo:live <pid> | head -40
   ```
3. 必要时导出 heap dump。
   ```bash
   jmap -dump:live,format=b,file=/tmp/heap.hprof <pid>
   ```
4. 检查 Metaspace、Direct Buffer、线程数和类加载数量。

#### 常见原因
- 堆太小，正常流量下 Old 区长期高水位。
- 内存泄漏，静态集合、缓存、ThreadLocal、监听器未释放。
- Metaspace 泄漏，动态类或 classloader 未释放。
- 大对象或批量查询一次性加载太多数据。

#### 处置
- 紧急: 扩容实例或适当调大堆，降低流量。
- 根治: 分析 heap dump，修复泄漏或无界缓存。
- 优化: 调整 GC 参数，控制批处理大小，避免一次性加载大结果集。

### JVM Metaspace 与 ThreadLocal 泄漏

#### 现象
- Metaspace 持续上涨，类加载数量异常增加，Full GC 后也无法明显回落。
- heap dump 引用链显示业务对象被 `ThreadLocalMap`、线程池线程、静态集合或 classloader 持有。
- 动态代理、脚本引擎、热加载、反射生成类、频繁创建 classloader 的模块更容易触发。

#### 排查步骤
1. 看类加载和 Metaspace。
   ```bash
   jstat -class <pid> 1000 10
   jcmd <pid> VM.native_memory summary
   ```
2. 导出 heap dump，用 MAT/VisualVM 查 dominator tree 和 GC roots。
3. ThreadLocal 泄漏重点看线程池长生命周期线程，确认业务代码是否在 `finally` 中 `remove()`。
4. Metaspace 泄漏重点看 classloader 是否被静态变量、线程上下文 classloader 或缓存引用。

#### 处置
- ThreadLocal: 在 finally 块调用 `remove()`，避免把 request、session、大对象放进长生命周期线程。
- Metaspace: 复用动态类生成器，释放 classloader 引用，限制脚本或模板热加载频率。
- 紧急止损: 回滚、重启异常实例、扩容，并保留 dump 用于根因分析。

## Kafka 故障

### Consumer Lag 持续增长

#### 现象
- consumer group lag 持续增长，消息处理延迟越来越大。
- 生产速率大于消费速率，或者单条消息卡住导致分区无法推进。

#### 排查步骤
1. 查看 consumer group lag。
   ```bash
   kafka-consumer-groups --bootstrap-server <broker> --describe --group <group>
   ```
2. 对比生产和消费速率，确认是整体吞吐不足还是个别分区卡住。
3. 检查 consumer 日志，定位 poison message、反序列化失败、下游写入超时。
4. 检查分区数与 consumer 实例数。consumer 数超过分区数不会继续提升并行度。

#### 处置
- 吞吐不足: 增加 consumer 实例，必要时增加 topic 分区数。
- 下游慢: 优化 DB/HTTP 写入，批量提交，增加超时和重试隔离。
- poison message: 跳过或转入死信队列，避免卡住整个分区。
- 提交 offset 异常: 检查 auto commit、手动 commit 和 rebalance 日志。

### Kafka offset 提交异常与重复消费

#### 现象
- 消息已经处理，但 offset 未提交或提交失败，监控中的 lag 可能不下降。
- consumer 重启或 rebalance 后从旧 offset 恢复，导致已经处理的消息被重复消费。
- 如果在业务处理成功前错误提交 offset，则失败或重启后可能跳过尚未完成的消息。

#### 排查与处置
1. 检查 auto commit、手动 commit、rebalance 和 offset commit 失败日志。
2. 对比 consumer group 的 committed offset 与业务实际处理进度。
3. 保证业务处理成功后再提交 offset；处理失败时不要错误提交。
4. 对重复消费做好业务幂等，对 poison message 转入死信队列，避免单条消息阻塞分区。

## 链路追踪故障

### 调用链 P99 延迟突增

#### 排查步骤
1. 拉取异常时间窗口的 trace 样本，按 trace 总耗时排序。
2. 展开最长 trace，按 span duration 找最长一跳。
3. 对最长 span 对应服务继续下钻。
   - 看该服务自身 RT、错误率、CPU、GC。
   - 看其依赖 DB、Redis、HTTP 下游的 span。
   - 对比是否有近期发布、配置变更或流量突增。
4. 如果只有少数请求慢，检查大客户、大参数、慢 SQL、缓存 miss。

#### 处置
- 明确是新版本导致: 灰度回滚。
- 依赖慢: 限流、熔断、隔离线程池或扩容依赖。
- 单条 SQL/外部调用慢: 加缓存、索引、超时和降级。

## etcd 故障

### etcd 响应慢导致 Kubernetes API 卡顿

#### 现象
- kube-apiserver 请求慢，kubectl 卡顿。
- etcd fsync、commit、apply latency 升高。

#### 排查步骤
1. 查看 etcd endpoint 状态。
   ```bash
   etcdctl endpoint status --cluster -w table
   ```
   关注 leader、raft term、db size、is learner。
2. 查看 endpoint health。
   ```bash
   etcdctl endpoint health --cluster -w table
   ```
3. 检查磁盘 fsync 延迟。etcd 对磁盘延迟非常敏感，慢盘会导致整体卡顿。
4. 检查 DB size 是否接近 quota，默认常见为 2GB。
5. 检查网络抖动和 leader 频繁切换。

#### 处置
- DB 膨胀: compact 后 defrag。
   ```bash
   etcdctl compact <revision>
   etcdctl defrag --cluster
   ```
- 磁盘慢: 迁移到更高 IOPS SSD，避免和高 IO 业务共盘。
- 网络抖动: 检查节点间延迟和丢包。
- quota 接近上限: 清理无用对象，评估调大 quota。

### etcd DB size 接近 quota 的 compact 与 defrag

#### 排查与处置
1. 用 `etcdctl endpoint status --cluster -w table` 确认当前 revision、DB size 和 quota 使用情况。
2. 删除无用 Kubernetes 对象，减少继续写入和历史版本增长。
3. 对确认的 revision 执行 compact，清理历史 revision。
   ```bash
   etcdctl compact <revision>
   ```
4. compact 后执行 defrag，回收后端数据库空间。
   ```bash
   etcdctl defrag --cluster
   ```
5. etcd 对磁盘延迟敏感，操作期间持续观察 endpoint health、fsync 和 commit latency；容量确实不足时再评估调大 quota。
