# Spinnaker circuit breaker open

> Group: **CI/CD**  
> Service: **Spinnaker**  
> Exporter: `embedded-exporter`  
> Severity: **warning**  
> Duration (for): `5m`

## 现象 / Description

Circuit breaker {{ $labels.name }} is open on {{ $labels.instance }}, indicating repeated downstream failures.

## PromQL 查询

```promql
resilience4j_circuitbreaker_state{state="open"} == 1
```

## 故障定位

- 触发该告警时, 检查 Spinnaker 的相关指标和日志
- 严重等级: warning
- 来源: awesome-prometheus-alerts / CI/CD / Spinnaker
