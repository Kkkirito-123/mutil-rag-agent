# SMART status

> Group: **Basic resource monitoring**  
> Service: **S.M.A.R.T Device Monitoring**  
> Exporter: `smartctl-exporter`  
> Severity: **critical**

## 现象 / Description

Device has a SMART status failure on {{ $labels.instance }} drive {{ $labels.device }}

## PromQL 查询

```promql
smartctl_device_smart_status != 1
```

## 故障定位

- 触发该告警时, 检查 S.M.A.R.T Device Monitoring 的相关指标和日志
- 严重等级: critical
- 来源: awesome-prometheus-alerts / Basic resource monitoring / S.M.A.R.T Device Monitoring
