# SNMP device restarted

> Group: **Network and security**  
> Service: **SNMP**  
> Exporter: `snmp-exporter`  
> Severity: **info**

## 现象 / Description

SNMP device {{ $labels.instance }} has restarted (uptime < 5 minutes).

## PromQL 查询

```promql
sysUpTime / 100 < 300
```

## 处理建议 / Comments

sysUpTime is in centiseconds (hundredths of a second).

## 故障定位

- 触发该告警时, 检查 SNMP 的相关指标和日志
- 严重等级: info
- 来源: awesome-prometheus-alerts / Network and security / SNMP
