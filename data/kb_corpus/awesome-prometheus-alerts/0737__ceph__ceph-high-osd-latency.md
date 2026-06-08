# Ceph high OSD latency

> Group: **Storage**  
> Service: **Ceph**  
> Exporter: `embedded-exporter`  
> Severity: **warning**  
> Duration (for): `1m`

## 现象 / Description

Ceph Object Storage Daemon latency is high. Please check if it doesn't stuck in weird state.

## PromQL 查询

```promql
ceph_osd_apply_latency_ms > 5000
```

## 处理建议 / Comments

Threshold of 5000ms (5 seconds). Adjust based on your expected OSD performance.

## 故障定位

- 触发该告警时, 检查 Ceph 的相关指标和日志
- 严重等级: warning
- 来源: awesome-prometheus-alerts / Storage / Ceph
