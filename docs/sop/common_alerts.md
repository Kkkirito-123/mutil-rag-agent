# 通用告警处理手册

## 一、HTTP 5xx 错误率激增

### 触发条件
任意 5 分钟窗口, 5xx 错误率超过 1%, 持续 3 分钟。

### 排查思路 (RAIL 法则)

#### R - Recent changes (近期变更)
1. 看发布平台, 是否有刚上线的版本?
2. 看配置中心, 是否有刚改的配置?
3. 看流量看板, 是否有突发流量?

#### A - Alerts (相关告警)
- 同时段是否有上游/下游服务的告警?
- 是否有依赖中间件 (Redis / MySQL / Kafka) 的告警?

#### I - Issues (业务侧反馈)
- 客服群是否有用户投诉?
- 监控大盘的核心业务指标是否同步下跌?

#### L - Logs (日志)
- 抽样几条 5xx 请求的 traceId, 在日志平台搜全链路
- 关注 ERROR 级别堆栈, 找根因

### 处置原则
**优先回滚, 后查根因**。线上止损永远是第一位的。

---

## 二、磁盘使用率告警

### 阈值
- WARN: 80%
- CRITICAL: 90%

### 排查
```bash
# 1. 看哪个目录占的多
du -sh /var/* | sort -rh | head -10

# 2. 看大文件
find / -size +1G -type f 2>/dev/null

# 3. 看打开但已删除的文件 (常见于日志被 rm 但进程还持有)
lsof | grep deleted | sort -k7 -rh | head
```

### 处置
- 日志类: 配置 logrotate, 立即清理旧日志
- 临时文件: 清理 /tmp 和应用临时目录
- 监控: 加上预警, 不要等 90% 才动手

---

## 三、容器频繁重启 (CrashLoopBackOff)

### 排查
```bash
# 1. 看 Pod 状态
kubectl describe pod <pod_name>

# 2. 看上一次容器的日志
kubectl logs <pod_name> --previous

# 3. 看资源使用
kubectl top pod <pod_name>
```

### 常见原因
1. **OOMKilled**: 内存 limit 太小, 看 lastState.terminated.reason
2. **Liveness 失败**: 启动慢, 但 liveness 探针太严格
3. **依赖未就绪**: 下游 DB / Redis 连不上, 启动报错退出
4. **配置错误**: ConfigMap / Secret 缺失或格式错

### 处置
- OOM: 调大 memory limit, 或排查内存泄漏
- Liveness: 加 initialDelaySeconds 或 startupProbe
- 依赖: 加重试 + readiness 探针
- 配置: kubectl get configmap/secret 核对
