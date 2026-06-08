# Sidekiq queue size

> Group: **Runtimes**  
> Service: **Sidekiq**  
> Exporter: `strech-sidekiq-exporter`  
> Severity: **warning**  
> Duration (for): `1m`

## 现象 / Description

Sidekiq queue {{ $labels.name }} is growing ({{ $value }} enqueued jobs)

## PromQL 查询

```promql
sidekiq_queue_enqueued_jobs > 100
```

## 故障定位

- 触发该告警时, 检查 Sidekiq 的相关指标和日志
- 严重等级: warning
- 来源: awesome-prometheus-alerts / Runtimes / Sidekiq
