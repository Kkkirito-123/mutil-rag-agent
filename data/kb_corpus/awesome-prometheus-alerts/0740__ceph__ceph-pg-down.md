# Ceph PG down

> Group: **Storage**  
> Service: **Ceph**  
> Exporter: `embedded-exporter`  
> Severity: **critical**

## 现象 / Description

Some Ceph placement groups are down. Please ensure that all the data are available.

## PromQL 查询

```promql
ceph_pg_down > 0
```

## 故障定位

- 触发该告警时, 检查 Ceph 的相关指标和日志
- 严重等级: critical
- 来源: awesome-prometheus-alerts / Storage / Ceph
