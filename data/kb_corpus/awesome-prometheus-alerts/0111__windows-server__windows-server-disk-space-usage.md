# Windows Server disk Space Usage

> Group: **Basic resource monitoring**  
> Service: **Windows Server**  
> Exporter: `windows-exporter`  
> Severity: **critical**  
> Duration (for): `2m`

## 现象 / Description

Disk usage is more than 80%

## PromQL 查询

```promql
100 - 100 * (windows_logical_disk_free_bytes / windows_logical_disk_size_bytes) > 80 and windows_logical_disk_size_bytes > 0
```

## 故障定位

- 触发该告警时, 检查 Windows Server 的相关指标和日志
- 严重等级: critical
- 来源: awesome-prometheus-alerts / Basic resource monitoring / Windows Server
