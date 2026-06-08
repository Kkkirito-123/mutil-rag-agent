# Windows Server service Status

> Group: **Basic resource monitoring**  
> Service: **Windows Server**  
> Exporter: `windows-exporter`  
> Severity: **critical**  
> Duration (for): `1m`

## 现象 / Description

Windows Service state is not OK

## PromQL 查询

```promql
windows_service_status{status="ok"} != 1
```

## 故障定位

- 触发该告警时, 检查 Windows Server 的相关指标和日志
- 严重等级: critical
- 来源: awesome-prometheus-alerts / Basic resource monitoring / Windows Server
