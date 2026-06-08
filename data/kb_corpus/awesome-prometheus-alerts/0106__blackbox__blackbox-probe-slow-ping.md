# Blackbox probe slow ping

> Group: **Basic resource monitoring**  
> Service: **Blackbox**  
> Exporter: `blackbox-exporter`  
> Severity: **warning**  
> Duration (for): `1m`

## 现象 / Description

Blackbox ping took more than 1s

## PromQL 查询

```promql
probe_icmp_duration_seconds > 1
```

## 故障定位

- 触发该告警时, 检查 Blackbox 的相关指标和日志
- 严重等级: warning
- 来源: awesome-prometheus-alerts / Basic resource monitoring / Blackbox
