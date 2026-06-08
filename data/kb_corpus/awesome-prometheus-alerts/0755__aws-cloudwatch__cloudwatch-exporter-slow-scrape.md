# CloudWatch exporter slow scrape

> Group: **Cloud providers**  
> Service: **AWS CloudWatch**  
> Exporter: `prometheus-cloudwatch-exporter`  
> Severity: **warning**  
> Duration (for): `5m`

## 现象 / Description

CloudWatch exporter on {{ $labels.instance }} scrape is taking more than 5 minutes ({{ $value }}s). Consider reducing the number of metrics or splitting across multiple exporters.

## PromQL 查询

```promql
cloudwatch_exporter_scrape_duration_seconds > 300
```

## 故障定位

- 触发该告警时, 检查 AWS CloudWatch 的相关指标和日志
- 严重等级: warning
- 来源: awesome-prometheus-alerts / Cloud providers / AWS CloudWatch
