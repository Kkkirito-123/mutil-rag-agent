# APC UPS Less than 15 Minutes of battery time remaining

> Group: **Other**  
> Service: **APC UPS**  
> Exporter: `apcupsd_exporter`  
> Severity: **critical**

## 现象 / Description

Battery is almost empty (< 15 Minutes remaining)

## PromQL 查询

```promql
apcupsd_battery_time_left_seconds < 900
```

## 故障定位

- 触发该告警时, 检查 APC UPS 的相关指标和日志
- 严重等级: critical
- 来源: awesome-prometheus-alerts / Other / APC UPS
