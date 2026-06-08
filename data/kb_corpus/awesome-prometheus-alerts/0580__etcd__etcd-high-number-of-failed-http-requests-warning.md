# Etcd high number of failed HTTP requests warning

> Group: **Orchestrators**  
> Service: **Etcd**  
> Exporter: `embedded-exporter`  
> Severity: **warning**  
> Duration (for): `2m`

## 现象 / Description

More than 1% HTTP failure detected in Etcd

## PromQL 查询

```promql
sum(rate(etcd_http_failed_total[1m])) BY (method) / sum(rate(etcd_http_received_total[1m])) BY (method) > 0.01 and sum(rate(etcd_http_received_total[1m])) BY (method) > 0
```

## 处理建议 / Comments

These etcd_http_* metrics are from the etcd v2 API and do not exist in etcd 3.x. Remove these rules if running etcd 3.x.

## 故障定位

- 触发该告警时, 检查 Etcd 的相关指标和日志
- 严重等级: warning
- 来源: awesome-prometheus-alerts / Orchestrators / Etcd
