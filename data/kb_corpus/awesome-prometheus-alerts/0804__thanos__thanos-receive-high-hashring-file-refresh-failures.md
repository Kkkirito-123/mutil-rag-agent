# Thanos Receive High Hashring File Refresh Failures

> Group: **Observability**  
> Service: **Thanos**  
> Exporter: `thanos-receiver`  
> Severity: **warning**  
> Duration (for): `15m`

## 现象 / Description

Thanos Receive {{$labels.job}} is failing to refresh hashring file, {{$value | humanize}} of attempts failed.

## PromQL 查询

```promql
(sum by (job) (rate(thanos_receive_hashrings_file_errors_total[5m])) / sum by (job) (rate(thanos_receive_hashrings_file_refreshes_total[5m])) > 0) and sum by (job) (rate(thanos_receive_hashrings_file_refreshes_total[5m])) > 0
```

## 故障定位

- 触发该告警时, 检查 Thanos 的相关指标和日志
- 严重等级: warning
- 来源: awesome-prometheus-alerts / Observability / Thanos
