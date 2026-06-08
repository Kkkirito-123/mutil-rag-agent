# Envoy cluster health check failures

> Group: **Proxies, load balancers and service meshes**  
> Service: **Envoy**  
> Exporter: `embedded-exporter`  
> Severity: **warning**  
> Duration (for): `5m`

## 现象 / Description

Health checks are consistently failing in cluster {{ $labels.envoy_cluster_name }} on {{ $labels.instance }} ({{ $value }} in the last 5m)

## PromQL 查询

```promql
increase(envoy_cluster_health_check_failure[5m]) > 5
```

## 故障定位

- 触发该告警时, 检查 Envoy 的相关指标和日志
- 严重等级: warning
- 来源: awesome-prometheus-alerts / Proxies, load balancers and service meshes / Envoy
