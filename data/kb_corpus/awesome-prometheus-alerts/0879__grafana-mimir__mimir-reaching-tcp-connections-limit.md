# Mimir reaching TCP connections limit

> Group: **Observability**  
> Service: **Grafana Mimir**  
> Exporter: `embedded-exporter`  
> Severity: **critical**  
> Duration (for): `5m`

## 现象 / Description

Mimir instance {{ $labels.instance }} is using {{ printf "%.0f" $value }}% of its TCP connections limit.

## PromQL 查询

```promql
cortex_tcp_connections / cortex_tcp_connections_limit * 100 > 80 and cortex_tcp_connections_limit > 0
```

## 故障定位

- 触发该告警时, 检查 Grafana Mimir 的相关指标和日志
- 严重等级: critical
- 来源: awesome-prometheus-alerts / Observability / Grafana Mimir
