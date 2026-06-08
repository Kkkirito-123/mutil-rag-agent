# SNMP interface high bandwidth usage inbound

> Group: **Network and security**  
> Service: **SNMP**  
> Exporter: `snmp-exporter`  
> Severity: **warning**  
> Duration (for): `15m`

## 现象 / Description

Interface {{ $labels.ifDescr }} on {{ $labels.instance }} inbound utilization is above 80%.

## PromQL 查询

```promql
rate(ifHCInOctets{job=~"snmp.*"}[5m]) * 8 / ifSpeed > 0.80 and ifSpeed > 0
```

## 处理建议 / Comments

Threshold is a rough default. ifSpeed is a Gauge32 that maxes out at ~4.29 Gbps. For 10G+ interfaces, use ifHighSpeed (in Mbps) instead.

## 故障定位

- 触发该告警时, 检查 SNMP 的相关指标和日志
- 严重等级: warning
- 来源: awesome-prometheus-alerts / Network and security / SNMP
