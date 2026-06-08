# Systemd service crash looping

> Group: **Basic resource monitoring**  
> Service: **Systemd**  
> Exporter: `systemd-exporter`  
> Severity: **critical**  
> Duration (for): `5m`

## 现象 / Description

Systemd service {{ $labels.name }} has restarted {{ $value }} times in the last hour. (instance {{ $labels.instance }})

## PromQL 查询

```promql
increase(systemd_service_restart_total[1h]) > 5
```

## 故障定位

- 触发该告警时, 检查 Systemd 的相关指标和日志
- 严重等级: critical
- 来源: awesome-prometheus-alerts / Basic resource monitoring / Systemd
