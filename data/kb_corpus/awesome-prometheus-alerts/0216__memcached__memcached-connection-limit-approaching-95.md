# Memcached connection limit approaching (> 95%)

> Group: **Databases**  
> Service: **Memcached**  
> Exporter: `memcached-exporter`  
> Severity: **critical**  
> Duration (for): `2m`

## 现象 / Description

Memcached connection usage is above 95% on {{ $labels.instance }} (current value: {{ $value }}%)

## PromQL 查询

```promql
(memcached_current_connections / memcached_max_connections * 100) > 95 and memcached_max_connections > 0
```

## 故障定位

- 触发该告警时, 检查 Memcached 的相关指标和日志
- 严重等级: critical
- 来源: awesome-prometheus-alerts / Databases / Memcached
