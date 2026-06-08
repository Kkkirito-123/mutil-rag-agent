# Store connection slow

> Group: **Other**  
> Service: **Graph Node**  
> Exporter: `embedded-exporter`  
> Severity: **warning**

## 现象 / Description

Store connection is too slow to `{{$labels.pool}}` pool, `{{$labels.shard}}` shard in Graph node `{{$labels.instance}}`

## PromQL 查询

```promql
store_connection_wait_time_ms > 10
```

## 处理建议 / Comments

Threshold of 10ms. Adjust based on your expected database latency.

## 故障定位

- 触发该告警时, 检查 Graph Node 的相关指标和日志
- 严重等级: warning
- 来源: awesome-prometheus-alerts / Other / Graph Node
