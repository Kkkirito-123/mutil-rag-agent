# Cilium KVStoreMesh remote cluster not ready

> Group: **Network and security**  
> Service: **Cilium**  
> Exporter: `embedded-exporter`  
> Severity: **critical**  
> Duration (for): `5m`

## 现象 / Description

Cilium KVStoreMesh remote cluster {{ $labels.target_cluster }} is not ready from {{ $labels.source_cluster }}.

## PromQL 查询

```promql
count(cilium_kvstoremesh_remote_cluster_readiness_status < 1) by (source_cluster, target_cluster) > 0
```

## 故障定位

- 触发该告警时, 检查 Cilium 的相关指标和日志
- 严重等级: critical
- 来源: awesome-prometheus-alerts / Network and security / Cilium
