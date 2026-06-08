# Systemd timer missed trigger

> Group: **Basic resource monitoring**  
> Service: **Systemd**  
> Exporter: `systemd-exporter`  
> Severity: **warning**  
> Duration (for): `5m`

## 现象 / Description

Systemd timer {{ $labels.name }} has not triggered for over 24 hours. (instance {{ $labels.instance }})

## PromQL 查询

```promql
(time() - systemd_timer_last_trigger_seconds) / 3600 > 24 and systemd_timer_last_trigger_seconds > 0
```

## 处理建议 / Comments

Triggers if timer hasn't fired in 24 hours. Adjust threshold per timer schedule.

## 故障定位

- 触发该告警时, 检查 Systemd 的相关指标和日志
- 严重等级: warning
- 来源: awesome-prometheus-alerts / Basic resource monitoring / Systemd
