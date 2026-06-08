# OpenStack Nova tenant vCPU quota nearly exhausted

> Group: **Orchestrators**  
> Service: **OpenStack**  
> Exporter: `openstack-exporter`  
> Severity: **warning**

## 现象 / Description

Tenant {{ $labels.tenant }} has used over 90% of its vCPU quota

## PromQL 查询

```promql
openstack_nova_limits_vcpus_used / openstack_nova_limits_vcpus_max > 0.9 and openstack_nova_limits_vcpus_max > 0
```

## 处理建议 / Comments

A value of -1 for limits_vcpus_max means unlimited quota (no limit set).

## 故障定位

- 触发该告警时, 检查 OpenStack 的相关指标和日志
- 严重等级: warning
- 来源: awesome-prometheus-alerts / Orchestrators / OpenStack
