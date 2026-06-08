# Host conntrack limit

> Group: **Basic resource monitoring**  
> Service: **Host and hardware**  
> Exporter: `node-exporter`  
> Severity: **warning**  
> Duration (for): `5m`

## 现象 / Description

The number of conntrack is approaching limit

## PromQL 查询

```promql
(node_nf_conntrack_entries / node_nf_conntrack_entries_limit > 0.8) and node_nf_conntrack_entries_limit > 0
```

## 故障定位

- 触发该告警时, 检查 Host and hardware 的相关指标和日志
- 严重等级: warning
- 来源: awesome-prometheus-alerts / Basic resource monitoring / Host and hardware
