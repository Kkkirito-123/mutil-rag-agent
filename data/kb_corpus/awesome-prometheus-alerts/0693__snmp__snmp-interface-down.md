# SNMP interface down

> Group: **Network and security**  
> Service: **SNMP**  
> Exporter: `snmp-exporter`  
> Severity: **critical**  
> Duration (for): `2m`

## 现象 / Description

Interface {{ $labels.ifDescr }} on {{ $labels.instance }} is operationally down while administratively up.

## PromQL 查询

```promql
(ifOperStatus{job=~"snmp.*"} == 2) and on(instance, job, ifIndex) (ifAdminStatus{job=~"snmp.*"} == 1)
```

## 故障定位

- 触发该告警时, 检查 SNMP 的相关指标和日志
- 严重等级: critical
- 来源: awesome-prometheus-alerts / Network and security / SNMP
