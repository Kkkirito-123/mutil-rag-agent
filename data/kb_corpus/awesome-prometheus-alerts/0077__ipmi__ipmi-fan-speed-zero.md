# IPMI fan speed zero

> Group: **Basic resource monitoring**  
> Service: **IPMI**  
> Exporter: `ipmi-exporter`  
> Severity: **critical**  
> Duration (for): `5m`

## 现象 / Description

IPMI fan {{ $labels.name }} on {{ $labels.instance }} reports 0 RPM. The fan may have failed.

## PromQL 查询

```promql
ipmi_fan_speed_rpm == 0
```

## 故障定位

- 触发该告警时, 检查 IPMI 的相关指标和日志
- 严重等级: critical
- 来源: awesome-prometheus-alerts / Basic resource monitoring / IPMI
