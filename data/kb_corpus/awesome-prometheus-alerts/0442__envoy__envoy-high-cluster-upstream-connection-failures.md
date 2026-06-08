# Envoy high cluster upstream connection failures

> Group: **Proxies, load balancers and service meshes**  
> Service: **Envoy**  
> Exporter: `embedded-exporter`  
> Severity: **warning**  
> Duration (for): `5m`

## 现象 / Description

High rate of upstream connection failures in cluster {{ $labels.envoy_cluster_name }} on {{ $labels.instance }} ({{ $value }} in the last 5m)

## PromQL 查询

```promql
increase(envoy_cluster_upstream_cx_connect_fail[5m]) > 10
```

## 故障定位

- 触发该告警时, 检查 Envoy 的相关指标和日志
- 严重等级: warning
- 来源: awesome-prometheus-alerts / Proxies, load balancers and service meshes / Envoy
