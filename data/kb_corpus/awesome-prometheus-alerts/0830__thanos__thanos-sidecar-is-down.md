# Thanos Sidecar Is Down

> Group: **Observability**  
> Service: **Thanos**  
> Exporter: `thanos-component-absent`  
> Severity: **critical**  
> Duration (for): `5m`

## 现象 / Description

ThanosSidecar has disappeared. Prometheus target for the component cannot be discovered.

## PromQL 查询

```promql
absent(up{job=~".*thanos-sidecar.*"} == 1)
```

## 故障定位

- 触发该告警时, 检查 Thanos 的相关指标和日志
- 严重等级: critical
- 来源: awesome-prometheus-alerts / Observability / Thanos
