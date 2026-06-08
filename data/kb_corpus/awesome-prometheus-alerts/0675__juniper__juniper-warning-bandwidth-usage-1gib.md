# Juniper warning Bandwidth Usage 1GiB

> Group: **Network and security**  
> Service: **Juniper**  
> Exporter: `czerwonk-junos-exporter`  
> Severity: **warning**  
> Duration (for): `1m`

## 现象 / Description

Interface is getting saturated. (> 0.80GiB/s)

## PromQL 查询

```promql
rate(junos_interface_transmit_bytes[1m]) * 8 > 1e+9 * 0.80
```

## 故障定位

- 触发该告警时, 检查 Juniper 的相关指标和日志
- 严重等级: warning
- 来源: awesome-prometheus-alerts / Network and security / Juniper
