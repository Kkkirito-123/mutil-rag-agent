# Zookeeper Too Many Leaders

> Group: **Message brokers**  
> Service: **Zookeeper**  
> Exporter: `dabealu-zookeeper-exporter`  
> Severity: **critical**

## 现象 / Description

Zookeeper cluster has {{ $value }} nodes marked as leader (expected 1), indicating a split-brain

## PromQL 查询

```promql
sum(zk_server_leader) > 1
```

## 故障定位

- 触发该告警时, 检查 Zookeeper 的相关指标和日志
- 严重等级: critical
- 来源: awesome-prometheus-alerts / Message brokers / Zookeeper
