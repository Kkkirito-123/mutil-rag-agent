# Blackbox probe failed

> Group: **Basic resource monitoring**  
> Service: **Blackbox**  
> Exporter: `blackbox-exporter`  
> Severity: **critical**  
> Duration (for): `1m`

## 现象 / Description

Probe failed

## PromQL 查询

```promql
probe_success == 0
```

## 故障定位

- 触发该告警时, 检查 Blackbox 的相关指标和日志
- 严重等级: critical
- 来源: awesome-prometheus-alerts / Basic resource monitoring / Blackbox
