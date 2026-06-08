# OpenStack placement resource high usage

> Group: **Orchestrators**  
> Service: **OpenStack**  
> Exporter: `openstack-exporter`  
> Severity: **warning**  
> Duration (for): `5m`

## 现象 / Description

Resource {{ $labels.resourcetype }} on host {{ $labels.hostname }} usage exceeds 90% of its allocation

## PromQL 查询

```promql
openstack_placement_resource_usage / (openstack_placement_resource_total * openstack_placement_resource_allocation_ratio) > 0.9 and openstack_placement_resource_total > 0
```

## 处理建议 / Comments

This alert factors in the allocation ratio to compute effective capacity.
The threshold of 90% is a rough default. Adjust based on your allocation ratios and workload patterns.

## 故障定位

- 触发该告警时, 检查 OpenStack 的相关指标和日志
- 严重等级: warning
- 来源: awesome-prometheus-alerts / Orchestrators / OpenStack
