# IPMI collector down

> Group: **Basic resource monitoring**  
> Service: **IPMI**  
> Exporter: `ipmi-exporter`  
> Severity: **warning**  
> Duration (for): `5m`

## 现象 / Description

IPMI collector {{ $labels.collector }} on {{ $labels.instance }} failed to scrape sensor data. Check FreeIPMI tools and BMC connectivity.

## PromQL 查询

```promql
ipmi_up == 0
```

## 处理建议 / Comments

The ipmi_up metric is per-collector. A value of 0 means the collector could not retrieve data from the BMC.

## 故障定位

- 触发该告警时, 检查 IPMI 的相关指标和日志
- 严重等级: warning
- 来源: awesome-prometheus-alerts / Basic resource monitoring / IPMI
