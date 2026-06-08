# Ceph PG inconsistent

> Group: **Storage**  
> Service: **Ceph**  
> Exporter: `embedded-exporter`  
> Severity: **warning**

## 现象 / Description

Some Ceph placement groups are inconsistent. Data is available but inconsistent across nodes.

## PromQL 查询

```promql
ceph_pg_inconsistent > 0
```

## 故障定位

- 触发该告警时, 检查 Ceph 的相关指标和日志
- 严重等级: warning
- 来源: awesome-prometheus-alerts / Storage / Ceph
