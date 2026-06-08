# OpenStack Neutron subnet IP pool exhaustion

> Group: **Orchestrators**  
> Service: **OpenStack**  
> Exporter: `openstack-exporter`  
> Severity: **warning**

## 现象 / Description

Subnet {{ $labels.subnet_name }} on network {{ $labels.network_name }} has used over 90% of its IP pool

## PromQL 查询

```promql
openstack_neutron_network_ip_availabilities_used / openstack_neutron_network_ip_availabilities_total > 0.9 and openstack_neutron_network_ip_availabilities_total > 0
```

## 故障定位

- 触发该告警时, 检查 OpenStack 的相关指标和日志
- 严重等级: warning
- 来源: awesome-prometheus-alerts / Orchestrators / OpenStack
