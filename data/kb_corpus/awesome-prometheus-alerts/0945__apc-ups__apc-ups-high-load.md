# APC UPS high load

> Group: **Other**  
> Service: **APC UPS**  
> Exporter: `apcupsd_exporter`  
> Severity: **warning**

## 现象 / Description

UPS load is > 80%

## PromQL 查询

```promql
apcupsd_ups_load_percent > 80
```

## 故障定位

- 触发该告警时, 检查 APC UPS 的相关指标和日志
- 严重等级: warning
- 来源: awesome-prometheus-alerts / Other / APC UPS
