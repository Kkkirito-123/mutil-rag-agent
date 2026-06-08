# Ceph OSD near full

> Group: **Storage**  
> Service: **Ceph**  
> Exporter: `embedded-exporter`  
> Severity: **warning**  
> Duration (for): `5m`

## 现象 / Description

A Ceph OSD is dangerously full. Please add more disks.

## PromQL 查询

```promql
ceph_health_detail{name="OSD_NEARFULL"} == 1
```

## 处理建议 / Comments

Ceph internally triggers OSD_NEARFULL based on the nearfull_ratio (default 85%).
ceph_health_detail exposes named health checks as individual time series.

## 故障定位

- 触发该告警时, 检查 Ceph 的相关指标和日志
- 严重等级: warning
- 来源: awesome-prometheus-alerts / Storage / Ceph
