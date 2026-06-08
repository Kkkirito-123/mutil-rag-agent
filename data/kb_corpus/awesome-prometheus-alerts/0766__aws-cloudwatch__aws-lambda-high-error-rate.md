# AWS Lambda high error rate

> Group: **Cloud providers**  
> Service: **AWS CloudWatch**  
> Exporter: `prometheus-cloudwatch-exporter`  
> Severity: **warning**  
> Duration (for): `5m`

## 现象 / Description

Lambda function {{ $labels.function_name }} error rate is above 5% ({{ $value }}%).

## PromQL 查询

```promql
(aws_lambda_errors_sum / aws_lambda_invocations_sum) * 100 > 5 and aws_lambda_invocations_sum > 0
```

## 处理建议 / Comments

Requires Lambda Errors and Invocations metrics.

## 故障定位

- 触发该告警时, 检查 AWS CloudWatch 的相关指标和日志
- 严重等级: warning
- 来源: awesome-prometheus-alerts / Cloud providers / AWS CloudWatch
