# IPMI chassis cooling fault

> Group: **Basic resource monitoring**  
> Service: **IPMI**  
> Exporter: `ipmi-exporter`  
> Severity: **critical**

## 现象 / Description

IPMI reports a cooling/fan fault on {{ $labels.instance }}. Check fans and airflow.

## PromQL 查询

```promql
ipmi_chassis_cooling_fault_state == 0
```

## 处理建议 / Comments

The metric uses inverted logic: 1=no fault, 0=fault detected.

## 故障定位

- 触发该告警时, 检查 IPMI 的相关指标和日志
- 严重等级: critical
- 来源: awesome-prometheus-alerts / Basic resource monitoring / IPMI
