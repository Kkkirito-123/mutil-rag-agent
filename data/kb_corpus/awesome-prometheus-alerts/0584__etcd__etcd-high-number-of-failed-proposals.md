# Etcd high number of failed proposals

> Group: **Orchestrators**  
> Service: **Etcd**  
> Exporter: `embedded-exporter`  
> Severity: **warning**  
> Duration (for): `2m`

## 现象 / Description

Etcd server got {{ $value }} failed proposals in the past hour

## PromQL 查询

```promql
increase(etcd_server_proposals_failed_total[1h]) > 5
```

## 故障定位

- 触发该告警时, 检查 Etcd 的相关指标和日志
- 严重等级: warning
- 来源: awesome-prometheus-alerts / Orchestrators / Etcd
