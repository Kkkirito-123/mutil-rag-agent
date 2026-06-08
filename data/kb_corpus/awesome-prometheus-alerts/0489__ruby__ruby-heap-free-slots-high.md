# Ruby heap free slots high

> Group: **Runtimes**  
> Service: **Ruby**  
> Exporter: `ruby-exporter`  
> Severity: **warning**  
> Duration (for): `5m`

## 现象 / Description

Ruby heap has too many free slots (> 500k), memory fragmentation after large allocations

## PromQL 查询

```promql
ruby_heap_free_slots > 500000
```

## 故障定位

- 触发该告警时, 检查 Ruby 的相关指标和日志
- 严重等级: warning
- 来源: awesome-prometheus-alerts / Runtimes / Ruby
