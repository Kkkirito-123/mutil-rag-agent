# OpenStack load balancer not online

> Group: **Orchestrators**  
> Service: **OpenStack**  
> Exporter: `openstack-exporter`  
> Severity: **warning**  
> Duration (for): `5m`

## 现象 / Description

Load balancer {{ $labels.name }} ({{ $labels.id }}) operating status is {{ $labels.operating_status }}

## PromQL 查询

```promql
openstack_loadbalancer_loadbalancer_status{operating_status!="ONLINE"} > 0
```

## 故障定位

- 触发该告警时, 检查 OpenStack 的相关指标和日志
- 严重等级: warning
- 来源: awesome-prometheus-alerts / Orchestrators / OpenStack
