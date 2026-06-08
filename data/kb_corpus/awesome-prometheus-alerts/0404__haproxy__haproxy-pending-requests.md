# HAProxy pending requests

> Group: **Proxies, load balancers and service meshes**  
> Service: **HaProxy**  
> Exporter: `embedded-exporter-v2`  
> Severity: **warning**  
> Duration (for): `2m`

## 现象 / Description

Some HAProxy requests are pending on {{ $labels.proxy }} - {{ $value | printf "%.2f"}}

## PromQL 查询

```promql
sum by (proxy) (haproxy_backend_current_queue) > 0
```

## 处理建议 / Comments

haproxy_backend_current_queue is a gauge (current queue depth), not a counter.

## 故障定位

- 触发该告警时, 检查 HaProxy 的相关指标和日志
- 严重等级: warning
- 来源: awesome-prometheus-alerts / Proxies, load balancers and service meshes / HaProxy
