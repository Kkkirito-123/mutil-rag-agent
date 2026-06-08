# Etcd high fsync durations

> Group: **Orchestrators**  
> Service: **Etcd**  
> Exporter: `embedded-exporter`  
> Severity: **warning**  
> Duration (for): `2m`

## 现象 / Description

Etcd WAL fsync duration increasing, 99th percentile is over 0.5s

## PromQL 查询

```promql
histogram_quantile(0.99, sum(rate(etcd_disk_wal_fsync_duration_seconds_bucket[5m])) by (instance, le)) > 0.5
```

## 故障定位

- 触发该告警时, 检查 Etcd 的相关指标和日志
- 严重等级: warning
- 来源: awesome-prometheus-alerts / Orchestrators / Etcd
