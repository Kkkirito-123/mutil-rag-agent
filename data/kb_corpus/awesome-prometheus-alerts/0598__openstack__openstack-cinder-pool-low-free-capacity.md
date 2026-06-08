# OpenStack Cinder pool low free capacity

> Group: **Orchestrators**  
> Service: **OpenStack**  
> Exporter: `openstack-exporter`  
> Severity: **warning**  
> Duration (for): `5m`

## 现象 / Description

Cinder storage pool {{ $labels.name }} has less than 10% free capacity

## PromQL 查询

```promql
openstack_cinder_pool_capacity_free_gb / openstack_cinder_pool_capacity_total_gb < 0.1 and openstack_cinder_pool_capacity_total_gb > 0
```

## 故障定位

- 触发该告警时, 检查 OpenStack 的相关指标和日志
- 严重等级: warning
- 来源: awesome-prometheus-alerts / Orchestrators / OpenStack
