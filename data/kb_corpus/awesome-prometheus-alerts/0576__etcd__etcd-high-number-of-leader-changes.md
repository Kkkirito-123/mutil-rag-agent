# Etcd high number of leader changes

> Group: **Orchestrators**  
> Service: **Etcd**  
> Exporter: `embedded-exporter`  
> Severity: **warning**

## 现象 / Description

Etcd leader changed {{ $value }} times during 10 minutes

## PromQL 查询

```promql
increase(etcd_server_leader_changes_seen_total[10m]) > 2
```

## 故障定位

- 触发该告警时, 检查 Etcd 的相关指标和日志
- 严重等级: warning
- 来源: awesome-prometheus-alerts / Orchestrators / Etcd
