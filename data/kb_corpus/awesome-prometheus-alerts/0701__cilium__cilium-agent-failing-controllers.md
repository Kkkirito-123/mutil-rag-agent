# Cilium agent failing controllers

> Group: **Network and security**  
> Service: **Cilium**  
> Exporter: `embedded-exporter`  
> Severity: **warning**  
> Duration (for): `5m`

## 现象 / Description

Cilium agent {{ $labels.pod }} has {{ $value }} failing controller(s). Check cilium-agent logs for details.

## PromQL 查询

```promql
sum(cilium_controllers_failing{}) by (pod) > 0
```

## 处理建议 / Comments

Metric name depends on Cilium version. Use cilium_controllers_failing (older) or cilium_controllers_runs_total (1.14+).

## 故障定位

- 触发该告警时, 检查 Cilium 的相关指标和日志
- 严重等级: warning
- 来源: awesome-prometheus-alerts / Network and security / Cilium
