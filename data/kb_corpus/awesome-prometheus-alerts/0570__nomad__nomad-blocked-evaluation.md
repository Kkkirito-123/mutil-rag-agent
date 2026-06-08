# Nomad blocked evaluation

> Group: **Orchestrators**  
> Service: **Nomad**  
> Exporter: `embedded-exporter`  
> Severity: **warning**

## 现象 / Description

Nomad has {{ $value }} blocked evaluations. The cluster may lack resources to place allocations.

## PromQL 查询

```promql
nomad_nomad_blocked_evals_total_blocked > 0
```

## 故障定位

- 触发该告警时, 检查 Nomad 的相关指标和日志
- 严重等级: warning
- 来源: awesome-prometheus-alerts / Orchestrators / Nomad
