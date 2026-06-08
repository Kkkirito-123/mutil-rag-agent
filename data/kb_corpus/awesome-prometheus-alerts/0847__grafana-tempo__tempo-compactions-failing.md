# Tempo compactions failing

> Group: **Observability**  
> Service: **Grafana Tempo**  
> Exporter: `embedded-exporter`  
> Severity: **critical**  
> Duration (for): `1h`

## 现象 / Description

{{ $value }} compactions have failed in the past hour.

## PromQL 查询

```promql
sum by (job) (increase(tempodb_compaction_errors_total[1h])) > 2 and sum by (job) (increase(tempodb_compaction_errors_total[5m])) > 0
```

## 处理建议 / Comments

Uses a two-window approach: 1h for historical count and 5m to confirm the issue is ongoing.

## 故障定位

- 触发该告警时, 检查 Grafana Tempo 的相关指标和日志
- 严重等级: critical
- 来源: awesome-prometheus-alerts / Observability / Grafana Tempo
