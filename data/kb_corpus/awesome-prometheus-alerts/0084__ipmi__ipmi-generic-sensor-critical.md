# IPMI generic sensor critical

> Group: **Basic resource monitoring**  
> Service: **IPMI**  
> Exporter: `ipmi-exporter`  
> Severity: **critical**  
> Duration (for): `5m`

## 现象 / Description

IPMI sensor {{ $labels.name }} (type={{ $labels.type }}) on {{ $labels.instance }} is in critical state.

## PromQL 查询

```promql
ipmi_sensor_state == 2
```

## 处理建议 / Comments

Catches any sensor type not covered by the specific temperature/fan/voltage/current/power alerts.

## 故障定位

- 触发该告警时, 检查 IPMI 的相关指标和日志
- 严重等级: critical
- 来源: awesome-prometheus-alerts / Basic resource monitoring / IPMI
