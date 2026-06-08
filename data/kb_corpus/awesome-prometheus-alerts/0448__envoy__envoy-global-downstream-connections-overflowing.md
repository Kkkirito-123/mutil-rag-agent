# Envoy global downstream connections overflowing

> Group: **Proxies, load balancers and service meshes**  
> Service: **Envoy**  
> Exporter: `embedded-exporter`  
> Severity: **critical**

## 现象 / Description

Downstream connections are being rejected due to global connection limit on {{ $labels.instance }} ({{ $value }} in the last 5m)

## PromQL 查询

```promql
increase(envoy_listener_downstream_global_cx_overflow[5m]) > 5
```

## 故障定位

- 触发该告警时, 检查 Envoy 的相关指标和日志
- 严重等级: critical
- 来源: awesome-prometheus-alerts / Proxies, load balancers and service meshes / Envoy
