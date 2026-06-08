# SNMP interface high outbound error rate

> Group: **Network and security**  
> Service: **SNMP**  
> Exporter: `snmp-exporter`  
> Severity: **warning**  
> Duration (for): `5m`

## 现象 / Description

Interface {{ $labels.ifDescr }} on {{ $labels.instance }} has an outbound error rate above 5%.

## PromQL 查询

```promql
rate(ifOutErrors{job=~"snmp.*"}[5m]) / (rate(ifHCOutUcastPkts{job=~"snmp.*"}[5m]) + rate(ifHCOutBroadcastPkts{job=~"snmp.*"}[5m]) + rate(ifHCOutMulticastPkts{job=~"snmp.*"}[5m])) > 0.05 and (rate(ifHCOutUcastPkts{job=~"snmp.*"}[5m]) + rate(ifHCOutBroadcastPkts{job=~"snmp.*"}[5m]) + rate(ifHCOutMulticastPkts{job=~"snmp.*"}[5m])) > 0
```

## 处理建议 / Comments

Threshold is a rough default. Adjust based on your network environment.

## 故障定位

- 触发该告警时, 检查 SNMP 的相关指标和日志
- 严重等级: warning
- 来源: awesome-prometheus-alerts / Network and security / SNMP
