# Juniper switch down

> Group: **Network and security**  
> Service: **Juniper**  
> Exporter: `czerwonk-junos-exporter`  
> Severity: **critical**

## 现象 / Description

The switch appears to be down

## PromQL 查询

```promql
junos_up == 0
```

## 故障定位

- 触发该告警时, 检查 Juniper 的相关指标和日志
- 严重等级: critical
- 来源: awesome-prometheus-alerts / Network and security / Juniper
