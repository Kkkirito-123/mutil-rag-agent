# Windows Server memory Usage

> Group: **Basic resource monitoring**  
> Service: **Windows Server**  
> Exporter: `windows-exporter`  
> Severity: **warning**  
> Duration (for): `2m`

## 现象 / Description

Memory usage is more than 90%

## PromQL 查询

```promql
100 - ((windows_os_physical_memory_free_bytes / windows_cs_physical_memory_bytes) * 100) > 90
```

## 故障定位

- 触发该告警时, 检查 Windows Server 的相关指标和日志
- 严重等级: warning
- 来源: awesome-prometheus-alerts / Basic resource monitoring / Windows Server
