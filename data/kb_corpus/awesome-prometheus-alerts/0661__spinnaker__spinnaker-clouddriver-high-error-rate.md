# Spinnaker Clouddriver high error rate

> Group: **CI/CD**  
> Service: **Spinnaker**  
> Exporter: `embedded-exporter`  
> Severity: **warning**  
> Duration (for): `5m`

## 现象 / Description

Clouddriver 5xx error rate is {{ $value | humanizePercentage }} on {{ $labels.instance }}. Cloud operations may be failing.

## PromQL 查询

```promql
sum by (instance) (rate(controller_invocations_total{status="5xx", job=~".*clouddriver.*"}[5m])) / sum by (instance) (rate(controller_invocations_total{job=~".*clouddriver.*"}[5m])) > 0.05 and sum by (instance) (rate(controller_invocations_total{job=~".*clouddriver.*"}[5m])) > 0
```

## 故障定位

- 触发该告警时, 检查 Spinnaker 的相关指标和日志
- 严重等级: warning
- 来源: awesome-prometheus-alerts / CI/CD / Spinnaker
