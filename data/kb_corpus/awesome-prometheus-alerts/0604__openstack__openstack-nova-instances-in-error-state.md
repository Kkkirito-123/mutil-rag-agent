# OpenStack Nova instances in ERROR state

> Group: **Orchestrators**  
> Service: **OpenStack**  
> Exporter: `openstack-exporter`  
> Severity: **warning**  
> Duration (for): `5m`

## 现象 / Description

{{ $value }} Nova instances are in ERROR state

## PromQL 查询

```promql
sum(openstack_nova_server_status{status="ERROR"}) > 0
```

## 故障定位

- 触发该告警时, 检查 OpenStack 的相关指标和日志
- 严重等级: warning
- 来源: awesome-prometheus-alerts / Orchestrators / OpenStack
