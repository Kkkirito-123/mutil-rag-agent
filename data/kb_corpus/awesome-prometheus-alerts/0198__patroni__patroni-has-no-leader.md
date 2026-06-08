# Patroni has no Leader

> Group: **Databases**  
> Service: **Patroni**  
> Exporter: `embedded-exporter-patroni`  
> Severity: **critical**  
> Duration (for): `1m`

## 现象 / Description

A leader node (neither primary nor standby) cannot be found inside the cluster {{ $labels.scope }}

## PromQL 查询

```promql
(max by (scope) (patroni_primary) < 1) and (max by (scope) (patroni_standby_leader) < 1)
```

## 处理建议 / Comments

1m delay allows a restart without triggering an alert.

## 故障定位

- 触发该告警时, 检查 Patroni 的相关指标和日志
- 严重等级: critical
- 来源: awesome-prometheus-alerts / Databases / Patroni
