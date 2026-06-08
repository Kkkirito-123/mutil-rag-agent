# DigitalOcean exporter collection errors

> Group: **Cloud providers**  
> Service: **DigitalOcean**  
> Exporter: `digitalocean-exporter`  
> Severity: **warning**  
> Duration (for): `5m`

## 现象 / Description

DigitalOcean exporter {{ $labels.collector }} collector has {{ $value }} errors.

## PromQL 查询

```promql
increase(digitalocean_errors_total[5m]) > 3
```

## 故障定位

- 触发该告警时, 检查 DigitalOcean 的相关指标和日志
- 严重等级: warning
- 来源: awesome-prometheus-alerts / Cloud providers / DigitalOcean
