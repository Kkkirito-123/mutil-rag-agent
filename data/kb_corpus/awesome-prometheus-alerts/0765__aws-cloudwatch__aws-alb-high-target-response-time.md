# AWS ALB high target response time

> Group: **Cloud providers**  
> Service: **AWS CloudWatch**  
> Exporter: `prometheus-cloudwatch-exporter`  
> Severity: **warning**  
> Duration (for): `5m`

## 现象 / Description

ALB {{ $labels.load_balancer }} average target response time is above 2 seconds ({{ $value }}s).

## PromQL 查询

```promql
aws_applicationelb_target_response_time_average > 2
```

## 处理建议 / Comments

Requires ApplicationELB TargetResponseTime metric.

## 故障定位

- 触发该告警时, 检查 AWS CloudWatch 的相关指标和日志
- 严重等级: warning
- 来源: awesome-prometheus-alerts / Cloud providers / AWS CloudWatch
