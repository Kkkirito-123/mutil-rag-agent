# OpenStack Cinder volumes in error state

> Group: **Orchestrators**  
> Service: **OpenStack**  
> Exporter: `openstack-exporter`  
> Severity: **warning**  
> Duration (for): `5m`

## 现象 / Description

{{ $value }} Cinder volumes are in an error state

## PromQL 查询

```promql
openstack_cinder_volume_status_counter{status=~"error.*"} > 0
```

## 故障定位

- 触发该告警时, 检查 OpenStack 的相关指标和日志
- 严重等级: warning
- 来源: awesome-prometheus-alerts / Orchestrators / OpenStack
