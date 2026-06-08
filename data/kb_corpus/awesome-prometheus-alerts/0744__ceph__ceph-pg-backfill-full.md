# Ceph PG backfill full

> Group: **Storage**  
> Service: **Ceph**  
> Exporter: `embedded-exporter`  
> Severity: **warning**  
> Duration (for): `2m`

## 现象 / Description

Some Ceph placement groups are located on full Object Storage Daemon on cluster. Those PGs can be unavailable shortly. Please check OSDs, change weight or reconfigure CRUSH rules.

## PromQL 查询

```promql
ceph_pg_backfill_toofull > 0
```

## 故障定位

- 触发该告警时, 检查 Ceph 的相关指标和日志
- 严重等级: warning
- 来源: awesome-prometheus-alerts / Storage / Ceph
