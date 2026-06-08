# Zookeeper Not Ok

> Group: **Message brokers**  
> Service: **Zookeeper**  
> Exporter: `dabealu-zookeeper-exporter`  
> Severity: **warning**  
> Duration (for): `3m`

## 现象 / Description

Zookeeper instance {{ $labels.instance }} is not ok (ruok check failed)

## PromQL 查询

```promql
zk_ruok == 0
```

## 故障定位

- 触发该告警时, 检查 Zookeeper 的相关指标和日志
- 严重等级: warning
- 来源: awesome-prometheus-alerts / Message brokers / Zookeeper
