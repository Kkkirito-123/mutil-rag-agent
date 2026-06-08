# Memcached high eviction rate

> Group: **Databases**  
> Service: **Memcached**  
> Exporter: `memcached-exporter`  
> Severity: **warning**  
> Duration (for): `5m`

## 现象 / Description

Memcached is evicting items at a high rate on {{ $labels.instance }} ({{ $value }} evictions/s)

## PromQL 查询

```promql
rate(memcached_items_evicted_total[5m]) > 10
```

## 处理建议 / Comments

A sustained eviction rate indicates memory pressure. Consider increasing memcached memory limit or reducing cache usage. Threshold of 10 evictions/s is a rough default — adjust based on your workload.

## 故障定位

- 触发该告警时, 检查 Memcached 的相关指标和日志
- 严重等级: warning
- 来源: awesome-prometheus-alerts / Databases / Memcached
