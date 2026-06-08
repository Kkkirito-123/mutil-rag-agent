# Nats high CPU usage

> Group: **Message brokers**  
> Service: **Nats**  
> Exporter: `nats-exporter`  
> Severity: **warning**  
> Duration (for): `5m`

## 现象 / Description

NATS server is using more than 80% CPU for the last 5 minutes

## PromQL 查询

```promql
gnatsd_varz_cpu > 80
```

## 处理建议 / Comments

gnatsd_varz_cpu is a gauge reporting CPU percentage (0-100 scale).

## 故障定位

- 触发该告警时, 检查 Nats 的相关指标和日志
- 严重等级: warning
- 来源: awesome-prometheus-alerts / Message brokers / Nats
