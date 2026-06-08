# ClickHouse high network usage

> Group: **Databases**  
> Service: **Clickhouse**  
> Exporter: `embedded-exporter`  
> Severity: **warning**  
> Duration (for): `2m`

## 现象 / Description

High network usage. ClickHouse network usage exceeds 100MB/s.

## PromQL 查询

```promql
rate(ClickHouseProfileEvents_NetworkSendBytes[1m]) > 100*1024*1024 or rate(ClickHouseProfileEvents_NetworkReceiveBytes[1m]) > 100*1024*1024
```

## 处理建议 / Comments

Please replace the threshold with an appropriate value

## 故障定位

- 触发该告警时, 检查 Clickhouse 的相关指标和日志
- 严重等级: warning
- 来源: awesome-prometheus-alerts / Databases / Clickhouse
