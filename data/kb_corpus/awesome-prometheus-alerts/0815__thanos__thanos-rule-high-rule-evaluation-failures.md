# Thanos Rule High Rule Evaluation Failures

> Group: **Observability**  
> Service: **Thanos**  
> Exporter: `thanos-ruler`  
> Severity: **critical**  
> Duration (for): `5m`

## 现象 / Description

Thanos Rule {{$labels.instance}} is failing to evaluate {{$value | humanize}}% of rules.

## PromQL 查询

```promql
(sum by (job, instance) (rate(prometheus_rule_evaluation_failures_total{job=~".*thanos-rule.*"}[5m])) / sum by (job, instance) (rate(prometheus_rule_evaluations_total{job=~".*thanos-rule.*"}[5m])) * 100 > 5) and sum by (job, instance) (rate(prometheus_rule_evaluations_total{job=~".*thanos-rule.*"}[5m])) > 0
```

## 故障定位

- 触发该告警时, 检查 Thanos 的相关指标和日志
- 严重等级: critical
- 来源: awesome-prometheus-alerts / Observability / Thanos
