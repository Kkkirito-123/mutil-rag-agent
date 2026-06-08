# Ceph OSD reweighted

> Group: **Storage**  
> Service: **Ceph**  
> Exporter: `embedded-exporter`  
> Severity: **warning**  
> Duration (for): `2m`

## 现象 / Description

Ceph Object Storage Daemon takes too much time to resize.

## PromQL 查询

```promql
ceph_osd_weight < 1
```

## 故障定位

- 触发该告警时, 检查 Ceph 的相关指标和日志
- 严重等级: warning
- 来源: awesome-prometheus-alerts / Storage / Ceph
