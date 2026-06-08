# Loki request panic

> Group: **Observability**  
> Service: **Loki**  
> Exporter: `embedded-exporter`  
> Severity: **critical**

## 现象 / Description

{{ $labels.job }} is experiencing {{ $value | humanize }} panic(s) in the last 5 minutes.

## PromQL 查询

```promql
sum(increase(loki_panic_total[5m])) by (namespace, job) > 0
```

## 故障定位

- 触发该告警时, 检查 Loki 的相关指标和日志
- 严重等级: critical
- 来源: awesome-prometheus-alerts / Observability / Loki
