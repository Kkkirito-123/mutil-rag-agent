# HAProxy server healthcheck failure

> Group: **Proxies, load balancers and service meshes**  
> Service: **HaProxy**  
> Exporter: `embedded-exporter-v2`  
> Severity: **warning**

## 现象 / Description

Some server healthcheck are failing on {{ $labels.server }} ({{ $value }} in the last 1m)

## PromQL 查询

```promql
increase(haproxy_server_check_failures_total[1m]) > 2
```

## 故障定位

- 触发该告警时, 检查 HaProxy 的相关指标和日志
- 严重等级: warning
- 来源: awesome-prometheus-alerts / Proxies, load balancers and service meshes / HaProxy
