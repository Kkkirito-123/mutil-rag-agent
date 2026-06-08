# Etcd HTTP requests slow

> Group: **Orchestrators**  
> Service: **Etcd**  
> Exporter: `embedded-exporter`  
> Severity: **warning**  
> Duration (for): `2m`

## 现象 / Description

HTTP requests slowing down, 99th percentile is over 0.15s

## PromQL 查询

```promql
histogram_quantile(0.99, rate(etcd_http_successful_duration_seconds_bucket[1m])) > 0.15
```

## 处理建议 / Comments

This etcd_http_* metric is from the etcd v2 API and does not exist in etcd 3.x. Remove this rule if running etcd 3.x.

## 故障定位

- 触发该告警时, 检查 Etcd 的相关指标和日志
- 严重等级: warning
- 来源: awesome-prometheus-alerts / Orchestrators / Etcd
