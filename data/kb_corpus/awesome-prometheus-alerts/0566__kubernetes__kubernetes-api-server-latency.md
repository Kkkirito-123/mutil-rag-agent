# Kubernetes API server latency

> Group: **Orchestrators**  
> Service: **Kubernetes**  
> Exporter: `kubestate-exporter`  
> Severity: **warning**  
> Duration (for): `2m`

## 现象 / Description

Kubernetes API server has a 99th percentile latency of {{ $value }} seconds for {{ $labels.verb }} {{ $labels.resource }}.

## PromQL 查询

```promql
histogram_quantile(0.99, sum(rate(apiserver_request_duration_seconds_bucket{verb!~"(?:CONNECT|WATCHLIST|WATCH|PROXY)"} [10m])) WITHOUT (subresource)) > 1
```

## 故障定位

- 触发该告警时, 检查 Kubernetes 的相关指标和日志
- 严重等级: warning
- 来源: awesome-prometheus-alerts / Orchestrators / Kubernetes
