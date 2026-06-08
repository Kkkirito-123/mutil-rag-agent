# DigitalOcean active incidents

> Group: **Cloud providers**  
> Service: **DigitalOcean**  
> Exporter: `digitalocean-exporter`  
> Severity: **warning**

## 现象 / Description

DigitalOcean platform has {{ $value }} active incident(s).

## PromQL 查询

```promql
digitalocean_incidents_total > 0
```

## 故障定位

- 触发该告警时, 检查 DigitalOcean 的相关指标和日志
- 严重等级: warning
- 来源: awesome-prometheus-alerts / Cloud providers / DigitalOcean
