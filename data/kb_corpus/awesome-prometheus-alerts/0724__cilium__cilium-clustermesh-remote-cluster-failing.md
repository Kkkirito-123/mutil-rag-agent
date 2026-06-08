# Cilium ClusterMesh remote cluster failing

> Group: **Network and security**  
> Service: **Cilium**  
> Exporter: `embedded-exporter`  
> Severity: **critical**  
> Duration (for): `5m`

## 现象 / Description

Cilium ClusterMesh connectivity to remote cluster {{ $labels.target_cluster }} from {{ $labels.source_cluster }} is failing ({{ $value }} failures).

## PromQL 查询

```promql
sum(cilium_clustermesh_remote_cluster_failures) by (source_cluster, target_cluster) > 0
```

## 故障定位

- 触发该告警时, 检查 Cilium 的相关指标和日志
- 严重等级: critical
- 来源: awesome-prometheus-alerts / Network and security / Cilium
