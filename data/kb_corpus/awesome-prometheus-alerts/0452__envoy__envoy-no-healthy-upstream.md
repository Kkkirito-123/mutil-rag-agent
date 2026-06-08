# Envoy no healthy upstream

> Group: **Proxies, load balancers and service meshes**  
> Service: **Envoy**  
> Exporter: `embedded-exporter`  
> Severity: **critical**

## 现象 / Description

Upstream connection attempts failed because no healthy upstream was available in cluster {{ $labels.envoy_cluster_name }} on {{ $labels.instance }} ({{ $value }} in the last 5m)

## PromQL 查询

```promql
increase(envoy_cluster_upstream_cx_none_healthy[5m]) > 3
```

## 故障定位

- 触发该告警时, 检查 Envoy 的相关指标和日志
- 严重等级: critical
- 来源: awesome-prometheus-alerts / Proxies, load balancers and service meshes / Envoy
