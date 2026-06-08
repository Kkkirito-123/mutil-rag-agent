# OpenStack Neutron agent down

> Group: **Orchestrators**  
> Service: **OpenStack**  
> Exporter: `openstack-exporter`  
> Severity: **critical**  
> Duration (for): `2m`

## 现象 / Description

Neutron agent {{ $labels.hostname }} ({{ $labels.service }}) is down

## PromQL 查询

```promql
openstack_neutron_agent_state{adminState="up"} == 0
```

## 故障定位

- 触发该告警时, 检查 OpenStack 的相关指标和日志
- 严重等级: critical
- 来源: awesome-prometheus-alerts / Orchestrators / OpenStack
