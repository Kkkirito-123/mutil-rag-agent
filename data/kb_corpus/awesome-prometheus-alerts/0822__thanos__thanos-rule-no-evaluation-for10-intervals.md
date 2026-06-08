# Thanos Rule No Evaluation For10 Intervals

> Group: **Observability**  
> Service: **Thanos**  
> Exporter: `thanos-ruler`  
> Severity: **info**  
> Duration (for): `5m`

## 现象 / Description

Thanos Rule {{$labels.job}} has rule groups that did not evaluate for at least 10x of their expected interval.

## PromQL 查询

```promql
time() -  max by (job, instance, group) (prometheus_rule_group_last_evaluation_timestamp_seconds{job=~".*thanos-rule.*"})>10 * max by (job, instance, group) (prometheus_rule_group_interval_seconds{job=~".*thanos-rule.*"})
```

## 故障定位

- 触发该告警时, 检查 Thanos 的相关指标和日志
- 严重等级: info
- 来源: awesome-prometheus-alerts / Observability / Thanos
