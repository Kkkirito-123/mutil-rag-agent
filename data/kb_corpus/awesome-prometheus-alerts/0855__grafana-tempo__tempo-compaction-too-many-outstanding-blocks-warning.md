# Tempo compaction too many outstanding blocks warning

> Group: **Observability**  
> Service: **Grafana Tempo**  
> Exporter: `embedded-exporter`  
> Severity: **warning**  
> Duration (for): `6h`

## 现象 / Description

There are too many outstanding compaction blocks for {{ $labels.instance }}. Consider increasing compactor resources.

## PromQL 查询

```promql
sum by (instance) (tempodb_compaction_outstanding_blocks) > 100
```

## 处理建议 / Comments

Threshold of 100 blocks per compactor instance. Adjust based on your environment.

## 故障定位

- 触发该告警时, 检查 Grafana Tempo 的相关指标和日志
- 严重等级: warning
- 来源: awesome-prometheus-alerts / Observability / Grafana Tempo
