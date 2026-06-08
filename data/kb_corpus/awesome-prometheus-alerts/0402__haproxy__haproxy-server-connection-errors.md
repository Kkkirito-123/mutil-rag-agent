# HAProxy server connection errors

> Group: **Proxies, load balancers and service meshes**  
> Service: **HaProxy**  
> Exporter: `embedded-exporter-v2`  
> Severity: **critical**

## 现象 / Description

Too many connection errors to {{ $labels.proxy }} (> 100 req/s). Request throughput may be too high.

## PromQL 查询

```promql
(sum by (proxy) (rate(haproxy_server_connection_errors_total[1m]))) > 100
```

## 故障定位

- 触发该告警时, 检查 HaProxy 的相关指标和日志
- 严重等级: critical
- 来源: awesome-prometheus-alerts / Proxies, load balancers and service meshes / HaProxy
