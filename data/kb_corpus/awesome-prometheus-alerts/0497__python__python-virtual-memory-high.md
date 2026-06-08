# Python virtual memory high

> Group: **Runtimes**  
> Service: **Python**  
> Exporter: `python-exporter`  
> Severity: **warning**  
> Duration (for): `5m`

## 现象 / Description

Python process virtual memory is high (> 4GB)

## PromQL 查询

```promql
process_virtual_memory_bytes > 4e9
```

## 处理建议 / Comments

Threshold is a rough default. Adjust based on your application's expected memory footprint.

## 故障定位

- 触发该告警时, 检查 Python 的相关指标和日志
- 严重等级: warning
- 来源: awesome-prometheus-alerts / Runtimes / Python
