# OpenStack Neutron ports without IPs

> Group: **Orchestrators**  
> Service: **OpenStack**  
> Exporter: `openstack-exporter`  
> Severity: **warning**  
> Duration (for): `5m`

## 现象 / Description

{{ $value }} active ports have no IP addresses assigned

## PromQL 查询

```promql
openstack_neutron_ports_no_ips > 0
```

## 故障定位

- 触发该告警时, 检查 OpenStack 的相关指标和日志
- 严重等级: warning
- 来源: awesome-prometheus-alerts / Orchestrators / OpenStack
