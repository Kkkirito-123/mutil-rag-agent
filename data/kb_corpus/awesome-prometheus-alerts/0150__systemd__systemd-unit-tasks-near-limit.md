# Systemd unit tasks near limit

> Group: **Basic resource monitoring**  
> Service: **Systemd**  
> Exporter: `systemd-exporter`  
> Severity: **warning**  
> Duration (for): `5m`

## 现象 / Description

Systemd unit {{ $labels.name }} is using {{ $value | humanizePercentage }} of its task limit. (instance {{ $labels.instance }})

## PromQL 查询

```promql
systemd_unit_tasks_current / ignoring(type) systemd_unit_tasks_max > 0.9 and ignoring(type) systemd_unit_tasks_max > 0
```

## 故障定位

- 触发该告警时, 检查 Systemd 的相关指标和日志
- 严重等级: warning
- 来源: awesome-prometheus-alerts / Basic resource monitoring / Systemd
