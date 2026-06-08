# Envoy high downstream HTTP 4xx error rate

> Group: **Proxies, load balancers and service meshes**  
> Service: **Envoy**  
> Exporter: `embedded-exporter`  
> Severity: **warning**  
> Duration (for): `5m`

## 现象 / Description

More than 10% of downstream HTTP responses are 4xx on {{ $labels.instance }} ({{ $value | printf "%.1f" }}%)

## PromQL 查询

```promql
sum by (instance) (rate(envoy_http_downstream_rq_xx{envoy_response_code_class="4"}[5m])) / sum by (instance) (rate(envoy_http_downstream_rq_completed[5m])) * 100 > 10 and sum by (instance) (rate(envoy_http_downstream_rq_completed[5m])) > 0
```

## 故障定位

- 触发该告警时, 检查 Envoy 的相关指标和日志
- 严重等级: warning
- 来源: awesome-prometheus-alerts / Proxies, load balancers and service meshes / Envoy
