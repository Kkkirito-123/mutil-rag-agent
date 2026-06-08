# AWS RDS high database connections

> Group: **Cloud providers**  
> Service: **AWS CloudWatch**  
> Exporter: `prometheus-cloudwatch-exporter`  
> Severity: **warning**  
> Duration (for): `5m`

## 现象 / Description

RDS instance {{ $labels.dbinstance_identifier }} has {{ $value }} active connections.

## PromQL 查询

```promql
aws_rds_database_connections_average > 100
```

## 处理建议 / Comments

The threshold depends on the RDS instance class. Adjust based on your
instance type's max_connections parameter.

## 故障定位

- 触发该告警时, 检查 AWS CloudWatch 的相关指标和日志
- 严重等级: warning
- 来源: awesome-prometheus-alerts / Cloud providers / AWS CloudWatch
