# Tempo polls failing

> Group: **Observability**  
> Service: **Grafana Tempo**  
> Exporter: `embedded-exporter`  
> Severity: **critical**

## 现象 / Description

{{ $value }} blocklist polls have failed in the past hour.

## PromQL 查询

```promql
sum by (job) (increase(tempodb_blocklist_poll_errors_total[1h])) > 2 and sum by (job) (increase(tempodb_blocklist_poll_errors_total[5m])) > 0
```

## 故障定位

- 触发该告警时, 检查 Grafana Tempo 的相关指标和日志
- 严重等级: critical
- 来源: awesome-prometheus-alerts / Observability / Grafana Tempo
