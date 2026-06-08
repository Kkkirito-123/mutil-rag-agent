# Provider failed because get genesis timeout

> Group: **Other**  
> Service: **Graph Node**  
> Exporter: `embedded-exporter`  
> Severity: **critical**

## 现象 / Description

Timeout to get genesis for Provider `{{$labels.provider}}` in Graph node `{{$labels.instance}}`

## PromQL 查询

```promql
eth_rpc_status == 4
```

## 故障定位

- 触发该告警时, 检查 Graph Node 的相关指标和日志
- 严重等级: critical
- 来源: awesome-prometheus-alerts / Other / Graph Node
