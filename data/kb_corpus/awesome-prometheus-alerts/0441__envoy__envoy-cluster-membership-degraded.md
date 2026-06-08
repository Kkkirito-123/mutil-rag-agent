# Envoy cluster membership degraded

> Group: **Proxies, load balancers and service meshes**  
> Service: **Envoy**  
> Exporter: `embedded-exporter`  
> Severity: **warning**  
> Duration (for): `5m`

## 现象 / Description

Only {{ $value | printf "%.1f" }}% of members in cluster {{ $labels.envoy_cluster_name }} on {{ $labels.instance }} are healthy (threshold: 75%)

## PromQL 查询

```promql
envoy_cluster_membership_healthy / envoy_cluster_membership_total * 100 < 75 and envoy_cluster_membership_total > 0
```

## 故障定位

- 触发该告警时, 检查 Envoy 的相关指标和日志
- 严重等级: warning
- 来源: awesome-prometheus-alerts / Proxies, load balancers and service meshes / Envoy
