# Ceph PG unavailable

> Group: **Storage**  
> Service: **Ceph**  
> Exporter: `embedded-exporter`  
> Severity: **critical**  
> Duration (for): `1m`

## 现象 / Description

Some Ceph placement groups are unavailable.

## PromQL 查询

```promql
ceph_pg_total - ceph_pg_active > 0
```

## 故障定位

- 触发该告警时, 检查 Ceph 的相关指标和日志
- 严重等级: critical
- 来源: awesome-prometheus-alerts / Storage / Ceph
