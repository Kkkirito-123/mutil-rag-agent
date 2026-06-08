# Python GC objects uncollectable

> Group: **Runtimes**  
> Service: **Python**  
> Exporter: `python-exporter`  
> Severity: **warning**  
> Duration (for): `5m`

## 现象 / Description

Python has uncollectable objects ({{ $value }}), potential memory leak via reference cycles

## PromQL 查询

```promql
increase(python_gc_objects_uncollectable_total[5m]) > 1
```

## 故障定位

- 触发该告警时, 检查 Python 的相关指标和日志
- 严重等级: warning
- 来源: awesome-prometheus-alerts / Runtimes / Python
