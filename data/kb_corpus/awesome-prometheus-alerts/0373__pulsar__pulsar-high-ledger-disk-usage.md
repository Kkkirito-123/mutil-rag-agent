# Pulsar high ledger disk usage

> Group: **Message brokers**  
> Service: **Pulsar**  
> Exporter: `embedded-exporter`  
> Severity: **critical**  
> Duration (for): `1h`

## 现象 / Description

Observing Ledger Disk Usage (> 75%)

## PromQL 查询

```promql
sum(bookie_ledger_dir__pulsar_data_bookkeeper_ledgers_usage) by (kubernetes_pod_name) > 75
```

## 处理建议 / Comments

This metric name is path-dependent and may differ based on your BookKeeper data directory configuration.
Adjust the metric name to match your actual ledger directory path.

## 故障定位

- 触发该告警时, 检查 Pulsar 的相关指标和日志
- 严重等级: critical
- 来源: awesome-prometheus-alerts / Message brokers / Pulsar
