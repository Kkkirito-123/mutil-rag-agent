# Ceph monitor clock skew

> Group: **Storage**  
> Service: **Ceph**  
> Exporter: `embedded-exporter`  
> Severity: **warning**  
> Duration (for): `2m`

## 现象 / Description

Ceph monitor clock skew detected. Please check ntp and hardware clock settings

## PromQL 查询

```promql
abs(ceph_monitor_clock_skew_seconds) > 0.2
```

## 故障定位

- 触发该告警时, 检查 Ceph 的相关指标和日志
- 严重等级: warning
- 来源: awesome-prometheus-alerts / Storage / Ceph
