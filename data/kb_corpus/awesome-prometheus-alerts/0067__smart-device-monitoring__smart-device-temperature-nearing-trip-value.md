# SMART device temperature nearing trip value

> Group: **Basic resource monitoring**  
> Service: **S.M.A.R.T Device Monitoring**  
> Exporter: `smartctl-exporter`  
> Severity: **warning**

## 现象 / Description

Device temperature at 80% of trip value on {{ $labels.instance }} drive {{ $labels.device }}

## PromQL 查询

```promql
max_over_time(smartctl_device_temperature{temperature_type="current"} [10m]) >= on(device, instance) (smartctl_device_temperature{temperature_type="drive_trip"} * .80)
```

## 故障定位

- 触发该告警时, 检查 S.M.A.R.T Device Monitoring 的相关指标和日志
- 严重等级: warning
- 来源: awesome-prometheus-alerts / Basic resource monitoring / S.M.A.R.T Device Monitoring
