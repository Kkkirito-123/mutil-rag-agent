# APC UPS Battery nearly empty

> Group: **Other**  
> Service: **APC UPS**  
> Exporter: `apcupsd_exporter`  
> Severity: **critical**

## 现象 / Description

Battery is almost empty (< 10% left)

## PromQL 查询

```promql
apcupsd_battery_charge_percent < 10
```

## 故障定位

- 触发该告警时, 检查 APC UPS 的相关指标和日志
- 严重等级: critical
- 来源: awesome-prometheus-alerts / Other / APC UPS
