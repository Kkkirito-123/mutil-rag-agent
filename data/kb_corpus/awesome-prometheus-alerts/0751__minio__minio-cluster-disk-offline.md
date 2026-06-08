# Minio cluster disk offline

> Group: **Storage**  
> Service: **Minio**  
> Exporter: `embedded-exporter`  
> Severity: **critical**

## 现象 / Description

Minio cluster disk is offline

## PromQL 查询

```promql
minio_cluster_drive_offline_total > 0
```

## 故障定位

- 触发该告警时, 检查 Minio 的相关指标和日志
- 严重等级: critical
- 来源: awesome-prometheus-alerts / Storage / Minio
