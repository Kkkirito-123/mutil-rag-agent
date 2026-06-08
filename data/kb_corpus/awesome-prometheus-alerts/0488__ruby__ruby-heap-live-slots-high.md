# Ruby heap live slots high

> Group: **Runtimes**  
> Service: **Ruby**  
> Exporter: `ruby-exporter`  
> Severity: **warning**  
> Duration (for): `5m`

## 现象 / Description

Ruby heap has too many live slots (> 500k), heap bloat

## PromQL 查询

```promql
ruby_heap_live_slots > 500000
```

## 处理建议 / Comments

Threshold is a rough default. Adjust based on your application's normal heap size.

## 故障定位

- 触发该告警时, 检查 Ruby 的相关指标和日志
- 严重等级: warning
- 来源: awesome-prometheus-alerts / Runtimes / Ruby
