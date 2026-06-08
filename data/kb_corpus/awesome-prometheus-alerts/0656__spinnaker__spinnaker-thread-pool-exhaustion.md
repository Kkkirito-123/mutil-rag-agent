# Spinnaker thread pool exhaustion

> Group: **CI/CD**  
> Service: **Spinnaker**  
> Exporter: `embedded-exporter`  
> Severity: **warning**  
> Duration (for): `5m`

## 现象 / Description

Orca message handler thread pool has {{ $value }} blocked threads on {{ $labels.instance }}. Pipeline execution throughput is degraded.

## PromQL 查询

```promql
threadpool_blockingQueueSize > 0
```

## 故障定位

- 触发该告警时, 检查 Spinnaker 的相关指标和日志
- 严重等级: warning
- 来源: awesome-prometheus-alerts / CI/CD / Spinnaker
