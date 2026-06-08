# Envoy cluster membership empty

> Group: **Proxies, load balancers and service meshes**  
> Service: **Envoy**  
> Exporter: `embedded-exporter`  
> Severity: **critical**  
> Duration (for): `1m`

## 现象 / Description

Envoy cluster {{ $labels.envoy_cluster_name }} on {{ $labels.instance }} has no healthy members

## PromQL 查询

```promql
envoy_cluster_membership_healthy == 0
```

## 故障定位

- 触发该告警时, 检查 Envoy 的相关指标和日志
- 严重等级: critical
- 来源: awesome-prometheus-alerts / Proxies, load balancers and service meshes / Envoy
