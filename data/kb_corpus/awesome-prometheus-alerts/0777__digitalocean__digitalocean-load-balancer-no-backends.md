# DigitalOcean load balancer no backends

> Group: **Cloud providers**  
> Service: **DigitalOcean**  
> Exporter: `digitalocean-exporter`  
> Severity: **warning**  
> Duration (for): `1m`

## 现象 / Description

DigitalOcean load balancer {{ $labels.name }} ({{ $labels.ip }}) has no droplets attached.

## PromQL 查询

```promql
digitalocean_loadbalancer_droplets == 0
```

## 故障定位

- 触发该告警时, 检查 DigitalOcean 的相关指标和日志
- 严重等级: warning
- 来源: awesome-prometheus-alerts / Cloud providers / DigitalOcean
