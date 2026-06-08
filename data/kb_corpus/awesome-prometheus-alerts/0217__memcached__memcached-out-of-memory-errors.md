# Memcached out of memory errors

> Group: **Databases**  
> Service: **Memcached**  
> Exporter: `memcached-exporter`  
> Severity: **warning**  
> Duration (for): `5m`

## 现象 / Description

Memcached is returning out-of-memory errors on {{ $labels.instance }} ({{ $value }} errors/s)

## PromQL 查询

```promql
sum without (slab) (rate(memcached_slab_items_outofmemory_total[5m])) > 0.05
```

## 故障定位

- 触发该告警时, 检查 Memcached 的相关指标和日志
- 严重等级: warning
- 来源: awesome-prometheus-alerts / Databases / Memcached
