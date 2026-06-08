# HAProxy backend max active session > 80%

> Group: **Proxies, load balancers and service meshes**  
> Service: **HaProxy**  
> Exporter: `embedded-exporter-v2`  
> Severity: **warning**  
> Duration (for): `2m`

## 现象 / Description

Session limit from backend {{ $labels.proxy }} reached 80% of limit - {{ $value | printf "%.2f"}}%

## PromQL 查询

```promql
(haproxy_backend_current_sessions / haproxy_backend_limit_sessions * 100) > 80 and haproxy_backend_limit_sessions > 0
```

## 故障定位

- 触发该告警时, 检查 HaProxy 的相关指标和日志
- 严重等级: warning
- 来源: awesome-prometheus-alerts / Proxies, load balancers and service meshes / HaProxy
