# Host node overtemperature alarm

> Group: **Basic resource monitoring**  
> Service: **Host and hardware**  
> Exporter: `node-exporter`  
> Severity: **critical**

## 现象 / Description

Physical node temperature alarm triggered

## PromQL 查询

```promql
((node_hwmon_temp_crit_alarm_celsius == 1) or (node_hwmon_temp_alarm == 1))
```

## 故障定位

- 触发该告警时, 检查 Host and hardware 的相关指标和日志
- 严重等级: critical
- 来源: awesome-prometheus-alerts / Basic resource monitoring / Host and hardware
