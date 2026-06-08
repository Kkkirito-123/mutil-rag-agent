# Mimir gossip members count too high

> Group: **Observability**  
> Service: **Grafana Mimir**  
> Exporter: `embedded-exporter`  
> Severity: **warning**  
> Duration (for): `20m`

## 现象 / Description

Mimir gossip cluster has more members than expected.

## PromQL 查询

```promql
avg(memberlist_client_cluster_members_count{job=~".*(mimir|cortex).*"}) by (job) * 1.15 + 10 < max(memberlist_client_cluster_members_count{job=~".*(mimir|cortex).*"}) by (job)
```

## 故障定位

- 触发该告警时, 检查 Grafana Mimir 的相关指标和日志
- 严重等级: warning
- 来源: awesome-prometheus-alerts / Observability / Grafana Mimir
