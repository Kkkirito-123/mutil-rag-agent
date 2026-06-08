# OpenStack Neutron floating IPs associated but not active

> Group: **Orchestrators**  
> Service: **OpenStack**  
> Exporter: `openstack-exporter`  
> Severity: **warning**  
> Duration (for): `5m`

## 现象 / Description

{{ $value }} floating IPs are associated to a private IP but are not in ACTIVE state

## PromQL 查询

```promql
openstack_neutron_floating_ips_associated_not_active > 0
```

## 故障定位

- 触发该告警时, 检查 OpenStack 的相关指标和日志
- 严重等级: warning
- 来源: awesome-prometheus-alerts / Orchestrators / OpenStack
