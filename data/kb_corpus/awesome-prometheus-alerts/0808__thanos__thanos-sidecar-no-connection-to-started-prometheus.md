# Thanos Sidecar No Connection To Started Prometheus

> Group: **Observability**  
> Service: **Thanos**  
> Exporter: `thanos-sidecar`  
> Severity: **critical**  
> Duration (for): `5m`

## 现象 / Description

Thanos Sidecar {{$labels.instance}} is unhealthy.

## PromQL 查询

```promql
thanos_sidecar_prometheus_up == 0 and on (namespace, pod) prometheus_tsdb_data_replay_duration_seconds != 0
```

## 故障定位

- 触发该告警时, 检查 Thanos 的相关指标和日志
- 严重等级: critical
- 来源: awesome-prometheus-alerts / Observability / Thanos
