# Etcd no Leader

> Group: **Orchestrators**  
> Service: **Etcd**  
> Exporter: `embedded-exporter`  
> Severity: **critical**

## 现象 / Description

Etcd cluster have no leader

## PromQL 查询

```promql
etcd_server_has_leader == 0
```

## 故障定位

- 触发该告警时, 检查 Etcd 的相关指标和日志
- 严重等级: critical
- 来源: awesome-prometheus-alerts / Orchestrators / Etcd
