# HAproxy has no alive backends

> Group: **Proxies, load balancers and service meshes**  
> Service: **HaProxy**  
> Exporter: `embedded-exporter-v2`  
> Severity: **critical**

## 现象 / Description

HAProxy has no alive active or backup backends for {{ $labels.proxy }}

## PromQL 查询

```promql
haproxy_backend_active_servers + haproxy_backend_backup_servers == 0
```

## 故障定位

- 触发该告警时, 检查 HaProxy 的相关指标和日志
- 严重等级: critical
- 来源: awesome-prometheus-alerts / Proxies, load balancers and service meshes / HaProxy
