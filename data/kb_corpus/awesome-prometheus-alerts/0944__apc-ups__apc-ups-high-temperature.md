# APC UPS high temperature

> Group: **Other**  
> Service: **APC UPS**  
> Exporter: `apcupsd_exporter`  
> Severity: **warning**  
> Duration (for): `2m`

## 现象 / Description

Internal temperature is high ({{$value}}°C)

## PromQL 查询

```promql
apcupsd_internal_temperature_celsius >= 40
```

## 故障定位

- 触发该告警时, 检查 APC UPS 的相关指标和日志
- 严重等级: warning
- 来源: awesome-prometheus-alerts / Other / APC UPS
