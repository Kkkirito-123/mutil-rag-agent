# IPMI temperature sensor critical

> Group: **Basic resource monitoring**  
> Service: **IPMI**  
> Exporter: `ipmi-exporter`  
> Severity: **critical**

## 现象 / Description

IPMI temperature sensor {{ $labels.name }} on {{ $labels.instance }} is in critical state. Immediate attention required to prevent hardware damage.

## PromQL 查询

```promql
ipmi_temperature_state == 2
```

## 故障定位

- 触发该告警时, 检查 IPMI 的相关指标和日志
- 严重等级: critical
- 来源: awesome-prometheus-alerts / Basic resource monitoring / IPMI
