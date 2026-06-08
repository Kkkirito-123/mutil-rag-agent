# Istio latency 99 percentile

> Group: **Proxies, load balancers and service meshes**  
> Service: **Istio**  
> Exporter: `embedded-exporter`  
> Severity: **warning**  
> Duration (for): `1m`

## 现象 / Description

Istio p99 request latency is {{ $value }}ms (threshold: 1000ms).

## PromQL 查询

```promql
histogram_quantile(0.99, sum(rate(istio_request_duration_milliseconds_bucket[1m])) by (destination_canonical_service, destination_workload_namespace, le)) > 1000
```

## 故障定位

- 触发该告警时, 检查 Istio 的相关指标和日志
- 严重等级: warning
- 来源: awesome-prometheus-alerts / Proxies, load balancers and service meshes / Istio
