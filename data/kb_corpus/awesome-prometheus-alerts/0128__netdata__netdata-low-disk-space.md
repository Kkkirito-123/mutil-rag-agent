# Netdata low disk space

> Group: **Basic resource monitoring**  
> Service: **Netdata**  
> Exporter: `embedded-exporter`  
> Severity: **warning**  
> Duration (for): `5m`

## 现象 / Description

Netdata low disk space (> 80%)

## PromQL 查询

```promql
100 / netdata_disk_space_GB_average * netdata_disk_space_GB_average{dimension=~"avail|cached"} < 20 and netdata_disk_space_GB_average > 0
```

## 故障定位

- 触发该告警时, 检查 Netdata 的相关指标和日志
- 严重等级: warning
- 来源: awesome-prometheus-alerts / Basic resource monitoring / Netdata
