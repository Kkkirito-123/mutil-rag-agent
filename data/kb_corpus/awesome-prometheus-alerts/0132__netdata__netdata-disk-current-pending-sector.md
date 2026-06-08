# Netdata disk current pending sector

> Group: **Basic resource monitoring**  
> Service: **Netdata**  
> Exporter: `embedded-exporter`  
> Severity: **warning**

## 现象 / Description

Disk current pending sector

## PromQL 查询

```promql
netdata_smartd_log_current_pending_sector_count_sectors_average > 0
```

## 故障定位

- 触发该告警时, 检查 Netdata 的相关指标和日志
- 严重等级: warning
- 来源: awesome-prometheus-alerts / Basic resource monitoring / Netdata
