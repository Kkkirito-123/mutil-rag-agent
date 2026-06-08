# Host unusual network throughput in

> Group: **Basic resource monitoring**  
> Service: **Host and hardware**  
> Exporter: `node-exporter`  
> Severity: **warning**

## 现象 / Description

Host receive bandwidth is high (>80%).

## PromQL 查询

```promql
((rate(node_network_receive_bytes_total[5m]) / node_network_speed_bytes) > .80) and node_network_speed_bytes > 0
```

## 故障定位

- 触发该告警时, 检查 Host and hardware 的相关指标和日志
- 严重等级: warning
- 来源: awesome-prometheus-alerts / Basic resource monitoring / Host and hardware
