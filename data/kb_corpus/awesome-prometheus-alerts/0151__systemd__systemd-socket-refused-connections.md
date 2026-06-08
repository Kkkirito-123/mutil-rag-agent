# Systemd socket refused connections

> Group: **Basic resource monitoring**  
> Service: **Systemd**  
> Exporter: `systemd-exporter`  
> Severity: **warning**  
> Duration (for): `2m`

## 现象 / Description

Systemd socket {{ $labels.name }} is refusing connections. ({{ $value }} refused in last 5m, instance {{ $labels.instance }})

## PromQL 查询

```promql
delta(systemd_socket_refused_connections_total[5m]) > 3
```

## 处理建议 / Comments

systemd_socket_refused_connections_total is declared as Gauge by the exporter despite the _total suffix, so delta() is used instead of increase().

## 故障定位

- 触发该告警时, 检查 Systemd 的相关指标和日志
- 严重等级: warning
- 来源: awesome-prometheus-alerts / Basic resource monitoring / Systemd
