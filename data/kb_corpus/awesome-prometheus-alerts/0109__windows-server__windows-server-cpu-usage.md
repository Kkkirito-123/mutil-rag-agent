# Windows Server CPU Usage

> Group: **Basic resource monitoring**  
> Service: **Windows Server**  
> Exporter: `windows-exporter`  
> Severity: **warning**

## 现象 / Description

CPU Usage is more than 80%

## PromQL 查询

```promql
100 - (avg by (instance) (rate(windows_cpu_time_total{mode="idle"}[2m])) * 100) > 80
```

## 故障定位

- 触发该告警时, 检查 Windows Server 的相关指标和日志
- 严重等级: warning
- 来源: awesome-prometheus-alerts / Basic resource monitoring / Windows Server
