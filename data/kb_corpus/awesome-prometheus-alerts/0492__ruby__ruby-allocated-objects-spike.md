# Ruby allocated objects spike

> Group: **Runtimes**  
> Service: **Ruby**  
> Exporter: `ruby-exporter`  
> Severity: **warning**  
> Duration (for): `5m`

## 现象 / Description

Ruby is allocating objects at a high rate

## PromQL 查询

```promql
rate(ruby_allocated_objects_total[5m]) > 100000
```

## 故障定位

- 触发该告警时, 检查 Ruby 的相关指标和日志
- 严重等级: warning
- 来源: awesome-prometheus-alerts / Runtimes / Ruby
