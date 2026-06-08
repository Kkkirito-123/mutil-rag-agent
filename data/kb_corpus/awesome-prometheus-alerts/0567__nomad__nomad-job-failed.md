# Nomad job failed

> Group: **Orchestrators**  
> Service: **Nomad**  
> Exporter: `embedded-exporter`  
> Severity: **warning**

## 现象 / Description

Nomad job {{ $labels.job }} has {{ $value }} failed allocations.

## PromQL 查询

```promql
nomad_nomad_job_summary_failed > 0
```

## 故障定位

- 触发该告警时, 检查 Nomad 的相关指标和日志
- 严重等级: warning
- 来源: awesome-prometheus-alerts / Orchestrators / Nomad
