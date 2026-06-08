# Istio Pilot Duplicate Entry

> Group: **Proxies, load balancers and service meshes**  
> Service: **Istio**  
> Exporter: `embedded-exporter`  
> Severity: **critical**

## 现象 / Description

Istio Pilot has detected {{ $value }} duplicate Envoy cluster(s), indicating misconfigured DestinationRules or ServiceEntries.

## PromQL 查询

```promql
sum(pilot_duplicate_envoy_clusters{}) > 0
```

## 故障定位

- 触发该告警时, 检查 Istio 的相关指标和日志
- 严重等级: critical
- 来源: awesome-prometheus-alerts / Proxies, load balancers and service meshes / Istio
