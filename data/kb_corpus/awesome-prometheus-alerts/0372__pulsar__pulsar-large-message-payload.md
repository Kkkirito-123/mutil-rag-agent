# Pulsar large message payload

> Group: **Message brokers**  
> Service: **Pulsar**  
> Exporter: `embedded-exporter`  
> Severity: **warning**  
> Duration (for): `1h`

## 现象 / Description

Pulsar topic {{ $labels.topic }} has {{ $value }} message entries exceeding the maximum size bucket (> 1MB)

## PromQL 查询

```promql
sum(pulsar_entry_size_le_overflow > 0) by (topic)
```

## 处理建议 / Comments

pulsar_entry_size_le_overflow is the overflow bucket of Pulsar's non-standard histogram.
It counts message entries exceeding all defined size bounds.

## 故障定位

- 触发该告警时, 检查 Pulsar 的相关指标和日志
- 严重等级: warning
- 来源: awesome-prometheus-alerts / Message brokers / Pulsar
