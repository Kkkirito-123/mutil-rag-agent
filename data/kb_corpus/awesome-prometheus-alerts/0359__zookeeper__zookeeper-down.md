# Zookeeper Down

> Group: **Message brokers**  
> Service: **Zookeeper**  
> Exporter: `dabealu-zookeeper-exporter`  
> Severity: **critical**  
> Duration (for): `1m`

## 现象 / Description

Zookeeper down on instance {{ $labels.instance }}

## PromQL 查询

```promql
zk_up == 0
```

## 处理建议 / Comments

1m delay allows a restart without triggering an alert.

## 故障定位

- 触发该告警时, 检查 Zookeeper 的相关指标和日志
- 严重等级: critical
- 来源: awesome-prometheus-alerts / Message brokers / Zookeeper
