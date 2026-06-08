# IPMI temperature sensor warning

> Group: **Basic resource monitoring**  
> Service: **IPMI**  
> Exporter: `ipmi-exporter`  
> Severity: **warning**  
> Duration (for): `5m`

## 现象 / Description

IPMI temperature sensor {{ $labels.name }} on {{ $labels.instance }} is in warning state.

## PromQL 查询

```promql
ipmi_temperature_state == 1
```

## 处理建议 / Comments

State values: 0=nominal, 1=warning, 2=critical. Thresholds are defined in the BMC firmware.

## 故障定位

- 触发该告警时, 检查 IPMI 的相关指标和日志
- 严重等级: warning
- 来源: awesome-prometheus-alerts / Basic resource monitoring / IPMI
