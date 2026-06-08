# Memcached items too large

> Group: **Databases**  
> Service: **Memcached**  
> Exporter: `memcached-exporter`  
> Severity: **info**  
> Duration (for): `5m`

## 现象 / Description

Memcached is rejecting items exceeding max-item-size on {{ $labels.instance }} ({{ $value }} rejections in the last 5m)

## PromQL 查询

```promql
increase(memcached_item_too_large_total[5m]) > 3
```

## 故障定位

- 触发该告警时, 检查 Memcached 的相关指标和日志
- 严重等级: info
- 来源: awesome-prometheus-alerts / Databases / Memcached
