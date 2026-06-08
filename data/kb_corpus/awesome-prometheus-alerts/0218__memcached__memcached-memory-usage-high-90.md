# Memcached memory usage high (> 90%)

> Group: **Databases**  
> Service: **Memcached**  
> Exporter: `memcached-exporter`  
> Severity: **warning**  
> Duration (for): `5m`

## 现象 / Description

Memcached memory usage is above 90% on {{ $labels.instance }} (current value: {{ $value }}%)

## PromQL 查询

```promql
(memcached_current_bytes / memcached_limit_bytes * 100) > 90 and memcached_limit_bytes > 0
```

## 处理建议 / Comments

High memory usage is expected if the cache is well-utilized. This alert fires when it approaches the configured limit, which may cause evictions.

## 故障定位

- 触发该告警时, 检查 Memcached 的相关指标和日志
- 严重等级: warning
- 来源: awesome-prometheus-alerts / Databases / Memcached
