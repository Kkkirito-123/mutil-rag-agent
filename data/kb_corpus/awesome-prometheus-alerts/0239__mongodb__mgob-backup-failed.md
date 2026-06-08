# Mgob backup failed

> Group: **Databases**  
> Service: **MongoDB**  
> Exporter: `stefanprodan-mgob-exporter`  
> Severity: **critical**

## 现象 / Description

MongoDB backup has failed

## PromQL 查询

```promql
changes(mgob_scheduler_backup_total{status="500"}[1h]) > 0
```

## 故障定位

- 触发该告警时, 检查 MongoDB 的相关指标和日志
- 严重等级: critical
- 来源: awesome-prometheus-alerts / Databases / MongoDB
