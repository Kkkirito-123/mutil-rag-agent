# Cilium KVStoreMesh sync errors

> Group: **Network and security**  
> Service: **Cilium**  
> Exporter: `embedded-exporter`  
> Severity: **critical**  
> Duration (for): `5m`

## 现象 / Description

Cilium KVStoreMesh from {{ $labels.source_cluster }} is experiencing kvstore sync errors.

## PromQL 查询

```promql
sum(rate(cilium_kvstoremesh_kvstore_sync_errors_total[5m])) by (source_cluster) > 0.05
```

## 故障定位

- 触发该告警时, 检查 Cilium 的相关指标和日志
- 严重等级: critical
- 来源: awesome-prometheus-alerts / Network and security / Cilium
