# Cloudflare http 5xx error rate

> Group: **Network and security**  
> Service: **Cloudflare**  
> Exporter: `lablabs-cloudflare-exporter`  
> Severity: **critical**

## 现象 / Description

Cloudflare high HTTP 5xx error rate (> 5% for domain {{ $labels.zone }})

## PromQL 查询

```promql
(sum by (zone) (rate(cloudflare_zone_requests_status{status=~"^5.."}[5m])) / on (zone) sum by (zone) (rate(cloudflare_zone_requests_status[5m]))) * 100 > 5 and sum by (zone) (rate(cloudflare_zone_requests_status[5m])) > 0
```

## 故障定位

- 触发该告警时, 检查 Cloudflare 的相关指标和日志
- 严重等级: critical
- 来源: awesome-prometheus-alerts / Network and security / Cloudflare
