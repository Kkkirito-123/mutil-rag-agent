# Istio high request latency

> Group: **Proxies, load balancers and service meshes**  
> Service: **Istio**  
> Exporter: `embedded-exporter`  
> Severity: **warning**  
> Duration (for): `1m`

## 现象 / Description

Istio average request duration is {{ $value }}ms (> 100ms).

## PromQL 查询

```promql
rate(istio_request_duration_milliseconds_sum{reporter="destination"}[1m]) / rate(istio_request_duration_milliseconds_count{reporter="destination"}[1m]) > 100 and rate(istio_request_duration_milliseconds_count{reporter="destination"}[1m]) > 0
```

## 故障定位

- 触发该告警时, 检查 Istio 的相关指标和日志
- 严重等级: warning
- 来源: awesome-prometheus-alerts / Proxies, load balancers and service meshes / Istio
