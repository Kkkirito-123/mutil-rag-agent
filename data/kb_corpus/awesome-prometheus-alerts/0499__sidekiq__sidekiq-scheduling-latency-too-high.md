# Sidekiq scheduling latency too high

> Group: **Runtimes**  
> Service: **Sidekiq**  
> Exporter: `strech-sidekiq-exporter`  
> Severity: **critical**

## 现象 / Description

Sidekiq jobs are taking more than 1min to be picked up. Users may be seeing delays in background processing.

## PromQL 查询

```promql
max(sidekiq_queue_latency_seconds) > 60
```

## 故障定位

- 触发该告警时, 检查 Sidekiq 的相关指标和日志
- 严重等级: critical
- 来源: awesome-prometheus-alerts / Runtimes / Sidekiq
