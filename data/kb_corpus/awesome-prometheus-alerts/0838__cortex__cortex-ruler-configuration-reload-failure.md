# Cortex ruler configuration reload failure

> Group: **Observability**  
> Service: **Cortex**  
> Exporter: `embedded-exporter`  
> Severity: **warning**

## 现象 / Description

Cortex ruler configuration reload failure (instance {{ $labels.instance }})

## PromQL 查询

```promql
cortex_ruler_config_last_reload_successful != 1
```

## 故障定位

- 触发该告警时, 检查 Cortex 的相关指标和日志
- 严重等级: warning
- 来源: awesome-prometheus-alerts / Observability / Cortex
