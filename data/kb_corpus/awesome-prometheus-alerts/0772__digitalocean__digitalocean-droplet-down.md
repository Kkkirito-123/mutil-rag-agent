# DigitalOcean droplet down

> Group: **Cloud providers**  
> Service: **DigitalOcean**  
> Exporter: `digitalocean-exporter`  
> Severity: **critical**  
> Duration (for): `5m`

## 现象 / Description

DigitalOcean droplet {{ $labels.name }} ({{ $labels.id }}) in {{ $labels.region }} is not running.

## PromQL 查询

```promql
digitalocean_droplet_up == 0
```

## 故障定位

- 触发该告警时, 检查 DigitalOcean 的相关指标和日志
- 严重等级: critical
- 来源: awesome-prometheus-alerts / Cloud providers / DigitalOcean
