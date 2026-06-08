# Consul service healthcheck failed

> Group: **Orchestrators**  
> Service: **Consul**  
> Exporter: `consul-exporter`  
> Severity: **critical**  
> Duration (for): `1m`

## 现象 / Description

Service: `{{ $labels.service_name }}` Healthcheck: `{{ $labels.service_id }}`

## PromQL 查询

```promql
consul_catalog_service_node_healthy == 0
```

## 故障定位

- 触发该告警时, 检查 Consul 的相关指标和日志
- 严重等级: critical
- 来源: awesome-prometheus-alerts / Orchestrators / Consul
