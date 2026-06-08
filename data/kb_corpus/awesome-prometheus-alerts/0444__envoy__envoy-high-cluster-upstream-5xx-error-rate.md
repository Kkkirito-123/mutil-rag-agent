# Envoy high cluster upstream 5xx error rate

> Group: **Proxies, load balancers and service meshes**  
> Service: **Envoy**  
> Exporter: `embedded-exporter`  
> Severity: **critical**  
> Duration (for): `1m`

## 现象 / Description

More than 5% of upstream requests return 5xx in cluster {{ $labels.envoy_cluster_name }} on {{ $labels.instance }}

## PromQL 查询

```promql
rate(envoy_cluster_upstream_rq_xx{envoy_response_code_class="5"}[5m]) / rate(envoy_cluster_upstream_rq_completed[5m]) * 100 > 5 and rate(envoy_cluster_upstream_rq_completed[5m]) > 0
```

## 故障定位

- 触发该告警时, 检查 Envoy 的相关指标和日志
- 严重等级: critical
- 来源: awesome-prometheus-alerts / Proxies, load balancers and service meshes / Envoy
