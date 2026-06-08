# Netdata disk reallocated sectors

> Group: **Basic resource monitoring**  
> Service: **Netdata**  
> Exporter: `embedded-exporter`  
> Severity: **info**

## 现象 / Description

Disk reallocated sectors detected ({{ $value }} sectors)

## PromQL 查询

```promql
increase(netdata_smartd_log_reallocated_sectors_count_sectors_average[1m]) > 0
```

## 故障定位

- 触发该告警时, 检查 Netdata 的相关指标和日志
- 严重等级: info
- 来源: awesome-prometheus-alerts / Basic resource monitoring / Netdata
