# Spinnaker high API error rate

> Group: **CI/CD**  
> Service: **Spinnaker**  
> Exporter: `embedded-exporter`  
> Severity: **warning**  
> Duration (for): `5m`

## 现象 / Description

Spinnaker API 5xx error rate is {{ $value | humanizePercentage }} on {{ $labels.instance }}.

## PromQL 查询

```promql
sum by (instance) (rate(controller_invocations_total{status="5xx"}[5m])) / sum by (instance) (rate(controller_invocations_total[5m])) > 0.05 and sum by (instance) (rate(controller_invocations_total[5m])) > 0
```

## 处理建议 / Comments

The 5% threshold is a rough default. Adjust based on your traffic patterns.

## 故障定位

- 触发该告警时, 检查 Spinnaker 的相关指标和日志
- 严重等级: warning
- 来源: awesome-prometheus-alerts / CI/CD / Spinnaker
