# Ceph State

> Group: **Storage**  
> Service: **Ceph**  
> Exporter: `embedded-exporter`  
> Severity: **critical**  
> Duration (for): `1m`

## 现象 / Description

Ceph instance unhealthy

## PromQL 查询

```promql
ceph_health_status != 0
```

## 处理建议 / Comments

ceph_health_status: 0=HEALTH_OK, 1=HEALTH_WARN, 2=HEALTH_ERR.
This rule fires on any non-OK state. Split into ==1 (warning) and ==2 (critical) if you want separate severity levels.

## 故障定位

- 触发该告警时, 检查 Ceph 的相关指标和日志
- 严重等级: critical
- 来源: awesome-prometheus-alerts / Storage / Ceph
