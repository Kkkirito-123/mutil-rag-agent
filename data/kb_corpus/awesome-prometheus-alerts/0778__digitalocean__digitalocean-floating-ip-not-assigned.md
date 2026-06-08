# DigitalOcean floating IP not assigned

> Group: **Cloud providers**  
> Service: **DigitalOcean**  
> Exporter: `digitalocean-exporter`  
> Severity: **warning**

## 现象 / Description

DigitalOcean floating IP {{ $labels.ipv4 }} in {{ $labels.region }} is not assigned to any droplet.

## PromQL 查询

```promql
digitalocean_floating_ipv4_active == 0
```

## 故障定位

- 触发该告警时, 检查 DigitalOcean 的相关指标和日志
- 严重等级: warning
- 来源: awesome-prometheus-alerts / Cloud providers / DigitalOcean
