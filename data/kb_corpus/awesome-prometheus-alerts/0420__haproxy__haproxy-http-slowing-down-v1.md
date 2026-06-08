# HAProxy HTTP slowing down (v1)

> Group: **Proxies, load balancers and service meshes**  
> Service: **HaProxy**  
> Exporter: `haproxy-exporter-v1`  
> Severity: **warning**  
> Duration (for): `1m`

## 现象 / Description

Average request time is increasing

## PromQL 查询

```promql
avg by (backend) (haproxy_backend_http_total_time_average_seconds) > 1
```

## 故障定位

- 触发该告警时, 检查 HaProxy 的相关指标和日志
- 严重等级: warning
- 来源: awesome-prometheus-alerts / Proxies, load balancers and service meshes / HaProxy
