# Systemd unit inactive

> Group: **Basic resource monitoring**  
> Service: **Systemd**  
> Exporter: `systemd-exporter`  
> Severity: **warning**  
> Duration (for): `5m`

## 现象 / Description

Systemd unit {{ $labels.name }} is inactive. (instance {{ $labels.instance }})

## PromQL 查询

```promql
systemd_unit_state{state="inactive", type="service", name=~"your-critical-service.+"} == 1
```

## 处理建议 / Comments

Many units are legitimately inactive. You must adjust the name=~ filter to match your critical services.

## 故障定位

- 触发该告警时, 检查 Systemd 的相关指标和日志
- 严重等级: warning
- 来源: awesome-prometheus-alerts / Basic resource monitoring / Systemd
