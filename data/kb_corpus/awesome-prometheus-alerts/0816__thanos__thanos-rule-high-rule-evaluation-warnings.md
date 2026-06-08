# Thanos Rule High Rule Evaluation Warnings

> Group: **Observability**  
> Service: **Thanos**  
> Exporter: `thanos-ruler`  
> Severity: **info**  
> Duration (for): `15m`

## 现象 / Description

Thanos Rule {{$labels.instance}} has high number of evaluation warnings ({{ $value | humanize }}/s).

## PromQL 查询

```promql
sum by (job, instance) (rate(thanos_rule_evaluation_with_warnings_total[5m])) > 0.05
```

## 处理建议 / Comments

Threshold of 0.05/s avoids firing on transient single-event spikes.

## 故障定位

- 触发该告警时, 检查 Thanos 的相关指标和日志
- 严重等级: info
- 来源: awesome-prometheus-alerts / Observability / Thanos
