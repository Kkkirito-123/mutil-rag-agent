# APC UPS AC input outage

> Group: **Other**  
> Service: **APC UPS**  
> Exporter: `apcupsd_exporter`  
> Severity: **warning**

## 现象 / Description

UPS now running on battery (since {{$value | humanizeDuration}})

## PromQL 查询

```promql
apcupsd_battery_time_on_seconds > 0
```

## 故障定位

- 触发该告警时, 检查 APC UPS 的相关指标和日志
- 严重等级: warning
- 来源: awesome-prometheus-alerts / Other / APC UPS
