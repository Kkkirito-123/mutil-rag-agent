# Virtual Machine Memory Critical

> Group: **Basic resource monitoring**  
> Service: **VMware**  
> Exporter: `pryorda-vmware-exporter`  
> Severity: **critical**  
> Duration (for): `1m`

## 现象 / Description

High memory usage on {{ $labels.instance }}: {{ $value | printf "%.2f"}}%

## PromQL 查询

```promql
vmware_vm_mem_usage_average / 100 >= 90
```

## 故障定位

- 触发该告警时, 检查 VMware 的相关指标和日志
- 严重等级: critical
- 来源: awesome-prometheus-alerts / Basic resource monitoring / VMware
