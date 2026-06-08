# Mimir compactor skipped blocks

> Group: **Observability**  
> Service: **Grafana Mimir**  
> Exporter: `embedded-exporter`  
> Severity: **warning**  
> Duration (for): `5m`

## 现象 / Description

Mimir compactor has found {{ $value }} blocks that cannot be compacted (reason {{ $labels.reason }}).

## PromQL 查询

```promql
increase(cortex_compactor_blocks_marked_for_no_compaction_total[24h]) > 0
```

## 处理建议 / Comments

Using a 24h window as compaction skips are rare events.

## 故障定位

- 触发该告警时, 检查 Grafana Mimir 的相关指标和日志
- 严重等级: warning
- 来源: awesome-prometheus-alerts / Observability / Grafana Mimir
