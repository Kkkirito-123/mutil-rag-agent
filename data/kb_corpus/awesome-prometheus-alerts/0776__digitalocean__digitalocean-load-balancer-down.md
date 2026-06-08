# DigitalOcean load balancer down

> Group: **Cloud providers**  
> Service: **DigitalOcean**  
> Exporter: `digitalocean-exporter`  
> Severity: **critical**  
> Duration (for): `2m`

## 现象 / Description

DigitalOcean load balancer {{ $labels.name }} ({{ $labels.ip }}) is not active.

## PromQL 查询

```promql
digitalocean_loadbalancer_status == 0
```

## 故障定位

- 触发该告警时, 检查 DigitalOcean 的相关指标和日志
- 严重等级: critical
- 来源: awesome-prometheus-alerts / Cloud providers / DigitalOcean
