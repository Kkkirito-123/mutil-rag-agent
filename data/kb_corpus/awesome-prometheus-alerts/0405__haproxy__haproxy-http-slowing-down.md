# HAProxy HTTP slowing down

> Group: **Proxies, load balancers and service meshes**  
> Service: **HaProxy**  
> Exporter: `embedded-exporter-v2`  
> Severity: **warning**  
> Duration (for): `1m`

## 现象 / Description

HAProxy backend max total time is above 1s on {{ $labels.proxy }} - {{ $value | printf "%.2f"}}s

## PromQL 查询

```promql
avg by (instance, proxy) (haproxy_backend_max_total_time_seconds) > 1
```

## 故障定位

- 触发该告警时, 检查 HaProxy 的相关指标和日志
- 严重等级: warning
- 来源: awesome-prometheus-alerts / Proxies, load balancers and service meshes / HaProxy
