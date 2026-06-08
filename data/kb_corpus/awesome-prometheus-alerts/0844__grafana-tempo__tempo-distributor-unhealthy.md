# Tempo distributor unhealthy

> Group: **Observability**  
> Service: **Grafana Tempo**  
> Exporter: `embedded-exporter`  
> Severity: **warning**  
> Duration (for): `15m`

## 现象 / Description

Tempo has {{ $value }} unhealthy distributor(s).

## PromQL 查询

```promql
max by (job) (tempo_ring_members{state="Unhealthy", name="distributor"}) > 0
```

## 故障定位

- 触发该告警时, 检查 Grafana Tempo 的相关指标和日志
- 严重等级: warning
- 来源: awesome-prometheus-alerts / Observability / Grafana Tempo
