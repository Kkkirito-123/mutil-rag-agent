# Python GC generation 2 collections high

> Group: **Runtimes**  
> Service: **Python**  
> Exporter: `python-exporter`  
> Severity: **warning**  
> Duration (for): `5m`

## 现象 / Description

Python full GC (generation 2) is running too frequently, indicating memory pressure

## PromQL 查询

```promql
rate(python_gc_collections_total{generation="2"}[5m]) > 1
```

## 处理建议 / Comments

Gen2 collection rate > 1/s is very high. In most applications, gen2 runs are infrequent. Adjust threshold based on your workload.

## 故障定位

- 触发该告警时, 检查 Python 的相关指标和日志
- 严重等级: warning
- 来源: awesome-prometheus-alerts / Runtimes / Python
