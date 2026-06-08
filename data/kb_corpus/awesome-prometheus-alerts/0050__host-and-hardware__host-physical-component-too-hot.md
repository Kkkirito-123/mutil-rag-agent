# Host physical component too hot

> Group: **Basic resource monitoring**  
> Service: **Host and hardware**  
> Exporter: `node-exporter`  
> Severity: **warning**  
> Duration (for): `5m`

## 现象 / Description

Physical hardware component too hot

## PromQL 查询

```promql
node_hwmon_temp_celsius > node_hwmon_temp_max_celsius
```

## 故障定位

- 触发该告警时, 检查 Host and hardware 的相关指标和日志
- 严重等级: warning
- 来源: awesome-prometheus-alerts / Basic resource monitoring / Host and hardware
