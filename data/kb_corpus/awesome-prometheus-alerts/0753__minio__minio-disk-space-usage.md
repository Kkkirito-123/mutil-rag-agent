# Minio disk space usage

> Group: **Storage**  
> Service: **Minio**  
> Exporter: `embedded-exporter`  
> Severity: **warning**

## 现象 / Description

Minio available free space is low (< 10%)

## PromQL 查询

```promql
minio_cluster_capacity_raw_free_bytes / minio_cluster_capacity_raw_total_bytes * 100 < 10 and minio_cluster_capacity_raw_total_bytes > 0
```

## 故障定位

- 触发该告警时, 检查 Minio 的相关指标和日志
- 严重等级: warning
- 来源: awesome-prometheus-alerts / Storage / Minio
