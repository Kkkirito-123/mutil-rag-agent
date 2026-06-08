# Systemd socket high connections

> Group: **Basic resource monitoring**  
> Service: **Systemd**  
> Exporter: `systemd-exporter`  
> Severity: **warning**  
> Duration (for): `2m`

## 现象 / Description

Systemd socket {{ $labels.name }} has {{ $value }} active connections. (instance {{ $labels.instance }})

## PromQL 查询

```promql
systemd_socket_current_connections > 100
```

## 处理建议 / Comments

Threshold of 100 connections is arbitrary. Adjust to your workload.

## 故障定位

- 触发该告警时, 检查 Systemd 的相关指标和日志
- 严重等级: warning
- 来源: awesome-prometheus-alerts / Basic resource monitoring / Systemd
