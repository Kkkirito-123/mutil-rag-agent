# OpenStack hypervisor high memory usage

> Group: **Orchestrators**  
> Service: **OpenStack**  
> Exporter: `openstack-exporter`  
> Severity: **warning**  
> Duration (for): `5m`

## 现象 / Description

Hypervisor {{ $labels.hostname }} memory usage is above 90%

## PromQL 查询

```promql
openstack_nova_memory_used_bytes / openstack_nova_memory_available_bytes > 0.9 and openstack_nova_memory_available_bytes > 0
```

## 处理建议 / Comments

The threshold of 90% is a rough default. Adjust based on your overcommit ratio and workload patterns.

## 故障定位

- 触发该告警时, 检查 OpenStack 的相关指标和日志
- 严重等级: warning
- 来源: awesome-prometheus-alerts / Orchestrators / OpenStack
