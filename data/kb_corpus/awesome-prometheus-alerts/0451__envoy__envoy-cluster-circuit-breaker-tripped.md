# Envoy cluster circuit breaker tripped

> Group: **Proxies, load balancers and service meshes**  
> Service: **Envoy**  
> Exporter: `embedded-exporter`  
> Severity: **critical**

## 现象 / Description

Circuit breaker is open for cluster {{ $labels.envoy_cluster_name }} on {{ $labels.instance }}

## PromQL 查询

```promql
envoy_cluster_circuit_breakers_default_cx_open == 1 or envoy_cluster_circuit_breakers_default_rq_open == 1
```

## 故障定位

- 触发该告警时, 检查 Envoy 的相关指标和日志
- 严重等级: critical
- 来源: awesome-prometheus-alerts / Proxies, load balancers and service meshes / Envoy
