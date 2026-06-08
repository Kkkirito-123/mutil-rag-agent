# OpenStack Cinder tenant volume quota nearly exhausted

> Group: **Orchestrators**  
> Service: **OpenStack**  
> Exporter: `openstack-exporter`  
> Severity: **warning**

## 现象 / Description

Tenant {{ $labels.tenant }} has used over 90% of its volume storage quota

## PromQL 查询

```promql
openstack_cinder_limits_volume_used_gb / openstack_cinder_limits_volume_max_gb > 0.9 and openstack_cinder_limits_volume_max_gb > 0
```

## 故障定位

- 触发该告警时, 检查 OpenStack 的相关指标和日志
- 严重等级: warning
- 来源: awesome-prometheus-alerts / Orchestrators / OpenStack
