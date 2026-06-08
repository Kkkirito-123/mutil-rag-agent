# Tempo block list rising quickly

> Group: **Observability**  
> Service: **Grafana Tempo**  
> Exporter: `embedded-exporter`  
> Severity: **critical**  
> Duration (for): `15m`

## 现象 / Description

Tempo blocklist length is up {{ printf "%.0f" $value }}% over the last 7 days. Consider scaling compactors.

## PromQL 查询

```promql
(avg(tempodb_blocklist_length) / avg(tempodb_blocklist_length offset 7d) - 1) * 100 > 40 and avg(tempodb_blocklist_length offset 7d) > 0
```

## 处理建议 / Comments

Fires when the blocklist grows more than 40% over 7 days.

## 故障定位

- 触发该告警时, 检查 Grafana Tempo 的相关指标和日志
- 严重等级: critical
- 来源: awesome-prometheus-alerts / Observability / Grafana Tempo
