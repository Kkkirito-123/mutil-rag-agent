# Tempo bad overrides

> Group: **Observability**  
> Service: **Grafana Tempo**  
> Exporter: `embedded-exporter`  
> Severity: **critical**  
> Duration (for): `15m`

## 现象 / Description

{{ $labels.job }} failed to reload runtime overrides.

## PromQL 查询

```promql
sum by (job) (tempo_runtime_config_last_reload_successful == 0) > 0
```

## 故障定位

- 触发该告警时, 检查 Grafana Tempo 的相关指标和日志
- 严重等级: critical
- 来源: awesome-prometheus-alerts / Observability / Grafana Tempo
