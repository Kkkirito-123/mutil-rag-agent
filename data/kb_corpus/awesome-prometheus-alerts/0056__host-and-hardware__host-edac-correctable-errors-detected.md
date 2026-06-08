# Host EDAC Correctable Errors detected

> Group: **Basic resource monitoring**  
> Service: **Host and hardware**  
> Exporter: `node-exporter`  
> Severity: **info**

## 现象 / Description

Host {{ $labels.instance }} has had {{ printf "%.0f" $value }} correctable memory errors reported by EDAC in the last 1 minute.

## PromQL 查询

```promql
(increase(node_edac_correctable_errors_total[1m]) > 0)
```

## 故障定位

- 触发该告警时, 检查 Host and hardware 的相关指标和日志
- 严重等级: info
- 来源: awesome-prometheus-alerts / Basic resource monitoring / Host and hardware
