# OpenStack hypervisor high disk usage

> Group: **Orchestrators**  
> Service: **OpenStack**  
> Exporter: `openstack-exporter`  
> Severity: **warning**  
> Duration (for): `5m`

## 现象 / Description

Hypervisor {{ $labels.hostname }} local disk usage is above 90%

## PromQL 查询

```promql
openstack_nova_local_storage_used_bytes / openstack_nova_local_storage_available_bytes > 0.9 and openstack_nova_local_storage_available_bytes > 0
```

## 故障定位

- 触发该告警时, 检查 OpenStack 的相关指标和日志
- 严重等级: warning
- 来源: awesome-prometheus-alerts / Orchestrators / OpenStack
