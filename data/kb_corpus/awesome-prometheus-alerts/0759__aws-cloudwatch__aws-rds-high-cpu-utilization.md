# AWS RDS high CPU utilization

> Group: **Cloud providers**  
> Service: **AWS CloudWatch**  
> Exporter: `prometheus-cloudwatch-exporter`  
> Severity: **warning**  
> Duration (for): `15m`

## 现象 / Description

RDS instance {{ $labels.dbinstance_identifier }} CPU utilization is above 90% ({{ $value }}%).

## PromQL 查询

```promql
aws_rds_cpuutilization_average > 90
```

## 处理建议 / Comments

Requires RDS CPUUtilization metric configured in the CloudWatch exporter.

## 故障定位

- 触发该告警时, 检查 AWS CloudWatch 的相关指标和日志
- 严重等级: warning
- 来源: awesome-prometheus-alerts / Cloud providers / AWS CloudWatch
