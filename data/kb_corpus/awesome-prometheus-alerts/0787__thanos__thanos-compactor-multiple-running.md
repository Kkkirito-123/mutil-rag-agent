# Thanos Compactor Multiple Running

> Group: **Observability**  
> Service: **Thanos**  
> Exporter: `thanos-compactor`  
> Severity: **warning**  
> Duration (for): `5m`

## 现象 / Description

No more than one Thanos Compact instance should be running at once. There are {{$value}} instances running.

## PromQL 查询

```promql
sum by (job) (up{job=~".*thanos-compact.*"}) > 1
```

## 故障定位

- 触发该告警时, 检查 Thanos 的相关指标和日志
- 严重等级: warning
- 来源: awesome-prometheus-alerts / Observability / Thanos
