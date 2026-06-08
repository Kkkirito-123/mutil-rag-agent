# Netdata high cpu usage

> Group: **Basic resource monitoring**  
> Service: **Netdata**  
> Exporter: `embedded-exporter`  
> Severity: **warning**  
> Duration (for): `5m`

## 现象 / Description

Netdata high CPU usage (> 80%)

## PromQL 查询

```promql
netdata_cpu_cpu_percentage_average{dimension="idle"} < 20
```

## 处理建议 / Comments

This is a gauge metric (not a counter). Checking idle < 20% means CPU usage > 80%.

## 故障定位

- 触发该告警时, 检查 Netdata 的相关指标和日志
- 严重等级: warning
- 来源: awesome-prometheus-alerts / Basic resource monitoring / Netdata
