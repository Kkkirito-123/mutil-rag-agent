# Thanos Rule Rule Evaluation Latency High

> Group: **Observability**  
> Service: **Thanos**  
> Exporter: `thanos-ruler`  
> Severity: **warning**  
> Duration (for): `5m`

## 现象 / Description

Thanos Rule {{$labels.instance}} has higher evaluation latency than interval for {{$labels.rule_group}}.

## PromQL 查询

```promql
(sum by (job, instance, rule_group) (prometheus_rule_group_last_duration_seconds{job=~".*thanos-rule.*"}) > sum by (job, instance, rule_group) (prometheus_rule_group_interval_seconds{job=~".*thanos-rule.*"}))
```

## 故障定位

- 触发该告警时, 检查 Thanos 的相关指标和日志
- 严重等级: warning
- 来源: awesome-prometheus-alerts / Observability / Thanos
