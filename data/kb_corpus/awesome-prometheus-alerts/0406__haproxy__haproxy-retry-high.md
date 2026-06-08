# HAProxy retry high

> Group: **Proxies, load balancers and service meshes**  
> Service: **HaProxy**  
> Exporter: `embedded-exporter-v2`  
> Severity: **warning**  
> Duration (for): `2m`

## 现象 / Description

High rate of retry on {{ $labels.proxy }} - {{ $value | printf "%.2f"}}

## PromQL 查询

```promql
sum by (proxy) (rate(haproxy_backend_retry_warnings_total[1m])) > 10
```

## 故障定位

- 触发该告警时, 检查 HaProxy 的相关指标和日志
- 严重等级: warning
- 来源: awesome-prometheus-alerts / Proxies, load balancers and service meshes / HaProxy
