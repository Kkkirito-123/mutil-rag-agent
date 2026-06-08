# Python GC collections high

> Group: **Runtimes**  
> Service: **Python**  
> Exporter: `python-exporter`  
> Severity: **warning**  
> Duration (for): `5m`

## 现象 / Description

Python GC is collecting too many objects (> 10k/s), high allocation pressure

## PromQL 查询

```promql
rate(python_gc_objects_collected_total[5m]) > 10000
```

## 故障定位

- 触发该告警时, 检查 Python 的相关指标和日志
- 严重等级: warning
- 来源: awesome-prometheus-alerts / Runtimes / Python
