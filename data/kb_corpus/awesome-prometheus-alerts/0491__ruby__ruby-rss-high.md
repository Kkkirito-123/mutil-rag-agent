# Ruby RSS high

> Group: **Runtimes**  
> Service: **Ruby**  
> Exporter: `ruby-exporter`  
> Severity: **warning**  
> Duration (for): `5m`

## 现象 / Description

Ruby process RSS is high (> 1GB)

## PromQL 查询

```promql
ruby_rss > 1e9
```

## 故障定位

- 触发该告警时, 检查 Ruby 的相关指标和日志
- 严重等级: warning
- 来源: awesome-prometheus-alerts / Runtimes / Ruby
