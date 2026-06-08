# Spinnaker polling monitor items over threshold

> Group: **CI/CD**  
> Service: **Spinnaker**  
> Exporter: `embedded-exporter`  
> Severity: **critical**  
> Duration (for): `5m`

## 现象 / Description

Igor polling monitor {{ $labels.monitor }} for {{ $labels.partition }} has exceeded its item threshold, preventing pipeline triggers.

## PromQL 查询

```promql
sum by (monitor, partition) (pollingMonitor_itemsOverThreshold) > 0
```

## 处理建议 / Comments

When this threshold is exceeded, Igor stops triggering pipelines for the affected monitor.
See https://kb.armory.io/s/article/Hitting-Igor-s-caching-thresholds

## 故障定位

- 触发该告警时, 检查 Spinnaker 的相关指标和日志
- 严重等级: critical
- 来源: awesome-prometheus-alerts / CI/CD / Spinnaker
