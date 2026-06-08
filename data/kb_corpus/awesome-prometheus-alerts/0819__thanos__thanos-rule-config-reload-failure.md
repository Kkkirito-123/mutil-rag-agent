# Thanos Rule Config Reload Failure

> Group: **Observability**  
> Service: **Thanos**  
> Exporter: `thanos-ruler`  
> Severity: **info**  
> Duration (for): `5m`

## 现象 / Description

Thanos Rule {{$labels.job}} has not been able to reload its configuration.

## PromQL 查询

```promql
avg by (job, instance) (thanos_rule_config_last_reload_successful) != 1
```

## 故障定位

- 触发该告警时, 检查 Thanos 的相关指标和日志
- 严重等级: info
- 来源: awesome-prometheus-alerts / Observability / Thanos
