# Spinnaker polling monitor failures

> Group: **CI/CD**  
> Service: **Spinnaker**  
> Exporter: `embedded-exporter`  
> Severity: **warning**  
> Duration (for): `5m`

## 现象 / Description

Igor polling monitor is experiencing failures ({{ $value }} per second). CI/SCM integrations may not trigger pipelines.

## PromQL 查询

```promql
rate(pollingMonitor_failed_total[5m]) > 0.05
```

## 故障定位

- 触发该告警时, 检查 Spinnaker 的相关指标和日志
- 严重等级: warning
- 来源: awesome-prometheus-alerts / CI/CD / Spinnaker
