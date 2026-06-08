# Tempo memcached errors elevated

> Group: **Observability**  
> Service: **Grafana Tempo**  
> Exporter: `embedded-exporter`  
> Severity: **warning**  
> Duration (for): `10m`

## 现象 / Description

Tempo memcached error rate is {{ printf "%.2f" $value }}% for {{ $labels.name }} in {{ $labels.job }}.

## PromQL 查询

```promql
100 * sum by (name, job) (rate(tempo_memcache_request_duration_seconds_count{status_code="500"}[5m])) / sum by (name, job) (rate(tempo_memcache_request_duration_seconds_count[5m])) > 20 and sum by (name, job) (rate(tempo_memcache_request_duration_seconds_count[5m])) > 0
```

## 处理建议 / Comments

Fires when the memcached error rate exceeds 20%. Only relevant if Tempo is configured with memcached caching.

## 故障定位

- 触发该告警时, 检查 Grafana Tempo 的相关指标和日志
- 严重等级: warning
- 来源: awesome-prometheus-alerts / Observability / Grafana Tempo
