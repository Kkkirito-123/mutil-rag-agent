# DigitalOcean droplet limit approaching

> Group: **Cloud providers**  
> Service: **DigitalOcean**  
> Exporter: `digitalocean-exporter`  
> Severity: **warning**

## 现象 / Description

DigitalOcean account is using {{ $value }}% of its droplet quota.

## PromQL 查询

```promql
(count(digitalocean_droplet_up) / digitalocean_account_droplet_limit) * 100 > 80 and digitalocean_account_droplet_limit > 0
```

## 处理建议 / Comments

Fires when more than 80% of the account's droplet limit is in use.

## 故障定位

- 触发该告警时, 检查 DigitalOcean 的相关指标和日志
- 严重等级: warning
- 来源: awesome-prometheus-alerts / Cloud providers / DigitalOcean
