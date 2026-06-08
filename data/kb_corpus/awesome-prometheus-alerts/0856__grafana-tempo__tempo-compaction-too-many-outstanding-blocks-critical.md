# Tempo compaction too many outstanding blocks critical

> Group: **Observability**  
> Service: **Grafana Tempo**  
> Exporter: `embedded-exporter`  
> Severity: **critical**  
> Duration (for): `24h`

## 现象 / Description

There are too many outstanding compaction blocks for {{ $labels.instance }}. Increase compactor resources immediately.

## PromQL 查询

```promql
sum by (instance) (tempodb_compaction_outstanding_blocks) > 250
```

## 处理建议 / Comments

Threshold of 100 blocks per compactor instance. Normalize by backend-worker count if needed. Adjust based on your environment.

## 故障定位

- 触发该告警时, 检查 Grafana Tempo 的相关指标和日志
- 严重等级: critical
- 来源: awesome-prometheus-alerts / Observability / Grafana Tempo
