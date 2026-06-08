# CloudWatch exporter scrape error

> Group: **Cloud providers**  
> Service: **AWS CloudWatch**  
> Exporter: `prometheus-cloudwatch-exporter`  
> Severity: **warning**  
> Duration (for): `5m`

## 现象 / Description

CloudWatch exporter on {{ $labels.instance }} failed to scrape metrics from AWS CloudWatch API.

## PromQL 查询

```promql
cloudwatch_exporter_scrape_error > 0
```

## 故障定位

- 触发该告警时, 检查 AWS CloudWatch 的相关指标和日志
- 严重等级: warning
- 来源: awesome-prometheus-alerts / Cloud providers / AWS CloudWatch
