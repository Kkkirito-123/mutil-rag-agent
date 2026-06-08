# Envoy high memory usage

> Group: **Proxies, load balancers and service meshes**  
> Service: **Envoy**  
> Exporter: `embedded-exporter`  
> Severity: **warning**  
> Duration (for): `5m`

## 现象 / Description

Envoy memory allocated is above 90% of heap size on {{ $labels.instance }}

## PromQL 查询

```promql
envoy_server_memory_allocated / envoy_server_memory_heap_size * 100 > 90 and envoy_server_memory_heap_size > 0
```

## 故障定位

- 触发该告警时, 检查 Envoy 的相关指标和日志
- 严重等级: warning
- 来源: awesome-prometheus-alerts / Proxies, load balancers and service meshes / Envoy
