# Ruby major GC rate high

> Group: **Runtimes**  
> Service: **Ruby**  
> Exporter: `ruby-exporter`  
> Severity: **warning**  
> Duration (for): `5m`

## 现象 / Description

Ruby is performing too many major GC cycles, indicating memory pressure

## PromQL 查询

```promql
rate(ruby_major_gc_ops_total[5m]) > 2
```

## 处理建议 / Comments

Major GC rate > 5/s only fires if the app is essentially non-functional. Threshold of 2/s provides earlier detection.

## 故障定位

- 触发该告警时, 检查 Ruby 的相关指标和日志
- 严重等级: warning
- 来源: awesome-prometheus-alerts / Runtimes / Ruby
