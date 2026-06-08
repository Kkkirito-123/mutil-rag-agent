# Pulsar high write latency

> Group: **Message brokers**  
> Service: **Pulsar**  
> Exporter: `embedded-exporter`  
> Severity: **critical**  
> Duration (for): `1h`

## 现象 / Description

Pulsar topic {{ $labels.topic }} has {{ $value }} storage write operations exceeding the maximum latency bucket (> 1000ms)

## PromQL 查询

```promql
sum(pulsar_storage_write_latency_le_overflow > 0) by (topic)
```

## 处理建议 / Comments

pulsar_storage_write_latency_le_overflow is the overflow bucket of Pulsar's non-standard histogram.
It counts write operations exceeding all defined latency bounds (> 1000ms).

## 故障定位

- 触发该告警时, 检查 Pulsar 的相关指标和日志
- 严重等级: critical
- 来源: awesome-prometheus-alerts / Message brokers / Pulsar
