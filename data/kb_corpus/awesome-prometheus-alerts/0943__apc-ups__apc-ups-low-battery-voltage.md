# APC UPS low battery voltage

> Group: **Other**  
> Service: **APC UPS**  
> Exporter: `apcupsd_exporter`  
> Severity: **warning**

## 现象 / Description

Battery voltage is lower than nominal (< 95%)

## PromQL 查询

```promql
(apcupsd_battery_volts / apcupsd_battery_nominal_volts) < 0.95 and apcupsd_battery_nominal_volts > 0
```

## 故障定位

- 触发该告警时, 检查 APC UPS 的相关指标和日志
- 严重等级: warning
- 来源: awesome-prometheus-alerts / Other / APC UPS
