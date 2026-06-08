# Etcd insufficient Members

> Group: **Orchestrators**  
> Service: **Etcd**  
> Exporter: `embedded-exporter`  
> Severity: **critical**

## 现象 / Description

Etcd cluster should have an odd number of members

## PromQL 查询

```promql
count(etcd_server_id) % 2 == 0
```

## 故障定位

- 触发该告警时, 检查 Etcd 的相关指标和日志
- 严重等级: critical
- 来源: awesome-prometheus-alerts / Orchestrators / Etcd
