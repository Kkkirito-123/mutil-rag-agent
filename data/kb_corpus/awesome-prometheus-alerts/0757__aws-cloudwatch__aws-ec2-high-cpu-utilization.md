# AWS EC2 high CPU utilization

> Group: **Cloud providers**  
> Service: **AWS CloudWatch**  
> Exporter: `prometheus-cloudwatch-exporter`  
> Severity: **warning**  
> Duration (for): `15m`

## 现象 / Description

EC2 instance {{ $labels.instance_id }} CPU utilization is above 90% ({{ $value }}%).

## PromQL 查询

```promql
aws_ec2_cpuutilization_average > 90
```

## 处理建议 / Comments

Requires EC2 CPUUtilization metric configured in the CloudWatch exporter.

## 故障定位

- 触发该告警时, 检查 AWS CloudWatch 的相关指标和日志
- 严重等级: warning
- 来源: awesome-prometheus-alerts / Cloud providers / AWS CloudWatch
