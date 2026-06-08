# OpenStack Nova tenant instance quota nearly exhausted

> Group: **Orchestrators**  
> Service: **OpenStack**  
> Exporter: `openstack-exporter`  
> Severity: **warning**

## 现象 / Description

Tenant {{ $labels.tenant }} has used over 90% of its instance quota

## PromQL 查询

```promql
openstack_nova_limits_instances_used / openstack_nova_limits_instances_max > 0.9 and openstack_nova_limits_instances_max > 0
```

## 故障定位

- 触发该告警时, 检查 OpenStack 的相关指标和日志
- 严重等级: warning
- 来源: awesome-prometheus-alerts / Orchestrators / OpenStack
