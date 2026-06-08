# ClickHouse node down

> Group: **Databases**  
> Service: **Clickhouse**  
> Exporter: `embedded-exporter`  
> Severity: **critical**  
> Duration (for): `2m`

## 现象 / Description

No metrics received from ClickHouse exporter for over 2 minutes.

## PromQL 查询

```promql
up{job="clickhouse"} == 0
```

## 处理建议 / Comments

Adjust the job label to match your Prometheus configuration.

## 故障定位

- 触发该告警时, 检查 Clickhouse 的相关指标和日志
- 严重等级: critical
- 来源: awesome-prometheus-alerts / Databases / Clickhouse
