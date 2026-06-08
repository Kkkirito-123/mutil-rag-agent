# HAProxy pending requests (v1)

> Group: **Proxies, load balancers and service meshes**  
> Service: **HaProxy**  
> Exporter: `haproxy-exporter-v1`  
> Severity: **warning**  
> Duration (for): `2m`

## 现象 / Description

Some HAProxy requests are pending on {{ $labels.backend }} backend

## PromQL 查询

```promql
sum by (backend) (haproxy_backend_current_queue) > 0
```

## 故障定位

- 触发该告警时, 检查 HaProxy 的相关指标和日志
- 严重等级: warning
- 来源: awesome-prometheus-alerts / Proxies, load balancers and service meshes / HaProxy
