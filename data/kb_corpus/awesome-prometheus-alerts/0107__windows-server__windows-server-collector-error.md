# Windows Server collector Error

> Group: **Basic resource monitoring**  
> Service: **Windows Server**  
> Exporter: `windows-exporter`  
> Severity: **critical**

## 现象 / Description

Collector {{ $labels.collector }} was not successful

## PromQL 查询

```promql
windows_exporter_collector_success == 0
```

## 故障定位

- 触发该告警时, 检查 Windows Server 的相关指标和日志
- 严重等级: critical
- 来源: awesome-prometheus-alerts / Basic resource monitoring / Windows Server
