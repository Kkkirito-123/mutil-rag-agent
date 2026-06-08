# CloudWatch API high request rate

> Group: **Cloud providers**  
> Service: **AWS CloudWatch**  
> Exporter: `prometheus-cloudwatch-exporter`  
> Severity: **warning**

## 现象 / Description

CloudWatch exporter on {{ $labels.instance }} is making {{ $value }} API calls per minute to namespace {{ $labels.namespace }}. This can lead to high AWS costs.

## PromQL 查询

```promql
sum by (instance, namespace) (rate(cloudwatch_requests_total[5m])) * 60 > 100
```

## 处理建议 / Comments

CloudWatch API calls cost money (~$0.01 per 1000 GetMetricData requests).
100 requests/minute ≈ $45/month. Adjust the threshold based on your budget.

## 故障定位

- 触发该告警时, 检查 AWS CloudWatch 的相关指标和日志
- 严重等级: warning
- 来源: awesome-prometheus-alerts / Cloud providers / AWS CloudWatch
