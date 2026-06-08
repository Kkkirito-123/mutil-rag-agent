# Netdata high memory usage

> Group: **Basic resource monitoring**  
> Service: **Netdata**  
> Exporter: `embedded-exporter`  
> Severity: **warning**  
> Duration (for): `5m`

## 现象 / Description

Netdata high memory usage (> 80%)

## PromQL 查询

```promql
100 / netdata_system_ram_MiB_average * netdata_system_ram_MiB_average{dimension=~"free|cached"} < 20 and netdata_system_ram_MiB_average > 0
```

## 故障定位

- 触发该告警时, 检查 Netdata 的相关指标和日志
- 严重等级: warning
- 来源: awesome-prometheus-alerts / Basic resource monitoring / Netdata
