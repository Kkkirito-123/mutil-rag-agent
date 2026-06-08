# AWS RDS low free storage space

> Group: **Cloud providers**  
> Service: **AWS CloudWatch**  
> Exporter: `prometheus-cloudwatch-exporter`  
> Severity: **warning**  
> Duration (for): `5m`

## 现象 / Description

RDS instance {{ $labels.dbinstance_identifier }} has less than 2GB free storage ({{ $value }} bytes remaining).

## PromQL 查询

```promql
aws_rds_free_storage_space_average < 2000000000
```

## 处理建议 / Comments

Requires RDS FreeStorageSpace metric. The threshold of 2GB is a rough default.
Adjust based on your database size.

## 故障定位

- 触发该告警时, 检查 AWS CloudWatch 的相关指标和日志
- 严重等级: warning
- 来源: awesome-prometheus-alerts / Cloud providers / AWS CloudWatch
