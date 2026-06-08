# AWS SQS queue messages visible

> Group: **Cloud providers**  
> Service: **AWS CloudWatch**  
> Exporter: `prometheus-cloudwatch-exporter`  
> Severity: **warning**  
> Duration (for): `10m`

## 现象 / Description

SQS queue {{ $labels.queue_name }} has {{ $value }} messages waiting to be processed.

## PromQL 查询

```promql
aws_sqs_approximate_number_of_messages_visible_average > 1000
```

## 处理建议 / Comments

Requires SQS ApproximateNumberOfMessagesVisible metric. The threshold of 1000
is a rough default. Adjust based on your expected queue depth.

## 故障定位

- 触发该告警时, 检查 AWS CloudWatch 的相关指标和日志
- 严重等级: warning
- 来源: awesome-prometheus-alerts / Cloud providers / AWS CloudWatch
