# Spinnaker zombie executions

> Group: **CI/CD**  
> Service: **Spinnaker**  
> Exporter: `embedded-exporter`  
> Severity: **warning**  
> Duration (for): `5m`

## 现象 / Description

Zombie pipeline executions rate is {{ $value | humanize }}/s. These are executions with no corresponding queue messages.

## PromQL 查询

```promql
rate(queue_zombies_total[5m]) > 0.05
```

## 处理建议 / Comments

Zombies are pipeline executions that are running but have lost their queue entry.
See https://spinnaker.io/docs/guides/runbooks/orca-zombie-executions/

## 故障定位

- 触发该告警时, 检查 Spinnaker 的相关指标和日志
- 严重等级: warning
- 来源: awesome-prometheus-alerts / CI/CD / Spinnaker
