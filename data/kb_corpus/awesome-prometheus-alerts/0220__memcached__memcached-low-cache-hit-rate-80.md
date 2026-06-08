# Memcached low cache hit rate (< 80%)

> Group: **Databases**  
> Service: **Memcached**  
> Exporter: `memcached-exporter`  
> Severity: **warning**  
> Duration (for): `10m`

## 现象 / Description

Memcached cache hit rate is below 80% on {{ $labels.instance }} (current value: {{ $value }}%)

## PromQL 查询

```promql
(rate(memcached_commands_total{command="get", status="hit"}[5m]) / (rate(memcached_commands_total{command="get", status="hit"}[5m]) + rate(memcached_commands_total{command="get", status="miss"}[5m])) * 100) < 80 and (rate(memcached_commands_total{command="get", status="hit"}[5m]) + rate(memcached_commands_total{command="get", status="miss"}[5m])) > 0
```

## 处理建议 / Comments

A low hit rate may indicate poor cache utilization, incorrect cache keys, or TTLs that are too short. Threshold of 80% is a rough default — adjust based on your workload and access patterns.

## 故障定位

- 触发该告警时, 检查 Memcached 的相关指标和日志
- 严重等级: warning
- 来源: awesome-prometheus-alerts / Databases / Memcached
