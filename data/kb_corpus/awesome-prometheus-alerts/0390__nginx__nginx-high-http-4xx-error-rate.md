# Nginx high HTTP 4xx error rate

> Group: **Proxies, load balancers and service meshes**  
> Service: **Nginx**  
> Exporter: `knyar-nginx-exporter`  
> Severity: **critical**  
> Duration (for): `1m`

## 现象 / Description

Too many HTTP requests with status 4xx (> 5%)

## PromQL 查询

```promql
sum(rate(nginx_http_requests_total{status=~"^4.."}[1m])) / sum(rate(nginx_http_requests_total[1m])) * 100 > 5 and sum(rate(nginx_http_requests_total[1m])) > 0
```

## 故障定位

- 触发该告警时, 检查 Nginx 的相关指标和日志
- 严重等级: critical
- 来源: awesome-prometheus-alerts / Proxies, load balancers and service meshes / Nginx
