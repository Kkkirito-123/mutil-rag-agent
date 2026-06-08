# Thanos Compactor Halted

> Group: **Observability**  
> Service: **Thanos**  
> Exporter: `thanos-compactor`  
> Severity: **warning**  
> Duration (for): `5m`

## 现象 / Description

Thanos Compact {{$labels.job}} has failed to run and now is halted.

## PromQL 查询

```promql
thanos_compact_halted == 1
```

## 故障定位

- 触发该告警时, 检查 Thanos 的相关指标和日志
- 严重等级: warning
- 来源: awesome-prometheus-alerts / Observability / Thanos
