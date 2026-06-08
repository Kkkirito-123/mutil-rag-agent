# AWS SQS message age too old

> Group: **Cloud providers**  
> Service: **AWS CloudWatch**  
> Exporter: `prometheus-cloudwatch-exporter`  
> Severity: **warning**

## 现象 / Description

SQS queue {{ $labels.queue_name }} has messages older than 1 hour ({{ $value }}s).

## PromQL 查询

```promql
aws_sqs_approximate_age_of_oldest_message_maximum > 3600
```

## 处理建议 / Comments

Requires SQS ApproximateAgeOfOldestMessage metric.

## 故障定位

- 触发该告警时, 检查 AWS CloudWatch 的相关指标和日志
- 严重等级: warning
- 来源: awesome-prometheus-alerts / Cloud providers / AWS CloudWatch
