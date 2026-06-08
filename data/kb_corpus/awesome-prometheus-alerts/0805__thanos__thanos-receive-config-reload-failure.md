# Thanos Receive Config Reload Failure

> Group: **Observability**  
> Service: **Thanos**  
> Exporter: `thanos-receiver`  
> Severity: **warning**  
> Duration (for): `5m`

## 现象 / Description

Thanos Receive {{$labels.job}} has not been able to reload hashring configurations.

## PromQL 查询

```promql
avg by (job) (thanos_receive_config_last_reload_successful) != 1
```

## 故障定位

- 触发该告警时, 检查 Thanos 的相关指标和日志
- 严重等级: warning
- 来源: awesome-prometheus-alerts / Observability / Thanos
