# Nginx latency high

> Group: **Proxies, load balancers and service meshes**  
> Service: **Nginx**  
> Exporter: `knyar-nginx-exporter`  
> Severity: **warning**  
> Duration (for): `2m`

## 现象 / Description

Nginx p99 latency is higher than 3 seconds

## PromQL 查询

```promql
histogram_quantile(0.99, sum(rate(nginx_http_request_duration_seconds_bucket[2m])) by (host, node, le)) > 3
```

## 故障定位

- 触发该告警时, 检查 Nginx 的相关指标和日志
- 严重等级: warning
- 来源: awesome-prometheus-alerts / Proxies, load balancers and service meshes / Nginx
