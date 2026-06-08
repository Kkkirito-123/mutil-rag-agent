# SNMP target down

> Group: **Network and security**  
> Service: **SNMP**  
> Exporter: `snmp-exporter`  
> Severity: **critical**  
> Duration (for): `5m`

## 现象 / Description

SNMP device {{ $labels.instance }} is unreachable.

## PromQL 查询

```promql
up{job=~"snmp.*"} == 0
```

## 处理建议 / Comments

Rename job=~"snmp.*" to match the actual job name in your Prometheus scrape config.

## 故障定位

- 触发该告警时, 检查 SNMP 的相关指标和日志
- 严重等级: critical
- 来源: awesome-prometheus-alerts / Network and security / SNMP
