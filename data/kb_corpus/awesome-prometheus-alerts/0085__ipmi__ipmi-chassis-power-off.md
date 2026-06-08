# IPMI chassis power off

> Group: **Basic resource monitoring**  
> Service: **IPMI**  
> Exporter: `ipmi-exporter`  
> Severity: **critical**

## 现象 / Description

IPMI reports chassis power is off on {{ $labels.instance }}. The server may have shut down unexpectedly.

## PromQL 查询

```promql
ipmi_chassis_power_state == 0
```

## 故障定位

- 触发该告警时, 检查 IPMI 的相关指标和日志
- 严重等级: critical
- 来源: awesome-prometheus-alerts / Basic resource monitoring / IPMI
