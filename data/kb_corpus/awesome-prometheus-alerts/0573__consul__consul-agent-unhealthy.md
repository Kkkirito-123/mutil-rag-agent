# Consul agent unhealthy

> Group: **Orchestrators**  
> Service: **Consul**  
> Exporter: `consul-exporter`  
> Severity: **critical**

## 现象 / Description

A Consul agent is down

## PromQL 查询

```promql
consul_health_node_status{status="critical"} == 1
```

## 故障定位

- 触发该告警时, 检查 Consul 的相关指标和日志
- 严重等级: critical
- 来源: awesome-prometheus-alerts / Orchestrators / Consul
