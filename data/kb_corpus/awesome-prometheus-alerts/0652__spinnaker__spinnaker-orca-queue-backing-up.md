# Spinnaker Orca queue backing up

> Group: **CI/CD**  
> Service: **Spinnaker**  
> Exporter: `embedded-exporter`  
> Severity: **warning**  
> Duration (for): `5m`

## 现象 / Description

Orca work queue has {{ $value }} messages ready for delivery but not yet picked up. Pipeline executions may be delayed.

## PromQL 查询

```promql
queue_ready_depth > 0
```

## 处理建议 / Comments

In a healthy Spinnaker, queue_ready_depth should stay at or near 0.
Sustained non-zero values indicate Orca cannot keep up with incoming work.

## 故障定位

- 触发该告警时, 检查 Spinnaker 的相关指标和日志
- 严重等级: warning
- 来源: awesome-prometheus-alerts / CI/CD / Spinnaker
