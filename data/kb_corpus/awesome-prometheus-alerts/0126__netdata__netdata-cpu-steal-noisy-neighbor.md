# Netdata CPU steal noisy neighbor

> Group: **Basic resource monitoring**  
> Service: **Netdata**  
> Exporter: `embedded-exporter`  
> Severity: **warning**  
> Duration (for): `5m`

## 现象 / Description

CPU steal is > 10%. A noisy neighbor is killing VM performances or a spot instance may be out of credit.

## PromQL 查询

```promql
netdata_cpu_cpu_percentage_average{dimension="steal"} > 10
```

## 故障定位

- 触发该告警时, 检查 Netdata 的相关指标和日志
- 严重等级: warning
- 来源: awesome-prometheus-alerts / Basic resource monitoring / Netdata
