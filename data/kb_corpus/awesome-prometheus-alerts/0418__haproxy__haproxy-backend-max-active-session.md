# HAProxy backend max active session

> Group: **Proxies, load balancers and service meshes**  
> Service: **HaProxy**  
> Exporter: `haproxy-exporter-v1`  
> Severity: **warning**  
> Duration (for): `2m`

## 现象 / Description

HAProxy backend {{ $labels.backend }} is reaching session limit (> 80%).

## PromQL 查询

```promql
((sum by (backend) (haproxy_backend_current_sessions * 100) / sum by (backend) (haproxy_backend_limit_sessions))) > 80 and sum by (backend) (haproxy_backend_limit_sessions) > 0
```

## 故障定位

- 触发该告警时, 检查 HaProxy 的相关指标和日志
- 严重等级: warning
- 来源: awesome-prometheus-alerts / Proxies, load balancers and service meshes / HaProxy
