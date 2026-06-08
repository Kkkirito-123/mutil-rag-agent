# Envoy high cluster upstream request timeout rate

> Group: **Proxies, load balancers and service meshes**  
> Service: **Envoy**  
> Exporter: `embedded-exporter`  
> Severity: **warning**  
> Duration (for): `5m`

## 现象 / Description

More than 5% of upstream requests are timing out in cluster {{ $labels.envoy_cluster_name }} on {{ $labels.instance }}

## PromQL 查询

```promql
rate(envoy_cluster_upstream_rq_timeout[5m]) / rate(envoy_cluster_upstream_rq_completed[5m]) * 100 > 5 and rate(envoy_cluster_upstream_rq_completed[5m]) > 0
```

## 故障定位

- 触发该告警时, 检查 Envoy 的相关指标和日志
- 严重等级: warning
- 来源: awesome-prometheus-alerts / Proxies, load balancers and service meshes / Envoy
