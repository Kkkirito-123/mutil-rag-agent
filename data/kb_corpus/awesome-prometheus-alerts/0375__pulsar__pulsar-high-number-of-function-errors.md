# Pulsar high number of function errors

> Group: **Message brokers**  
> Service: **Pulsar**  
> Exporter: `embedded-exporter`  
> Severity: **critical**  
> Duration (for): `1m`

## 现象 / Description

Pulsar function {{ $labels.name }} has more than 10 errors per second ({{ $value | printf "%.2f" }}/s)

## PromQL 查询

```promql
sum(rate(pulsar_function_user_exceptions_total[1m]) + rate(pulsar_function_system_exceptions_total[1m])) by (name) > 10
```

## 故障定位

- 触发该告警时, 检查 Pulsar 的相关指标和日志
- 严重等级: critical
- 来源: awesome-prometheus-alerts / Message brokers / Pulsar
