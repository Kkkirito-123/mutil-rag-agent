# Istio high 4xx error rate

> Group: **Proxies, load balancers and service meshes**  
> Service: **Istio**  
> Exporter: `embedded-exporter`  
> Severity: **warning**  
> Duration (for): `1m`

## 现象 / Description

High percentage of HTTP 4xx responses in Istio ({{ $value | printf "%.1f" }}% > 5%).

## PromQL 查询

```promql
sum(rate(istio_requests_total{reporter="destination", response_code=~"4.*"}[5m])) / sum(rate(istio_requests_total{reporter="destination"}[5m])) * 100 > 5 and sum(rate(istio_requests_total{reporter="destination"}[5m])) > 0
```

## 故障定位

- 触发该告警时, 检查 Istio 的相关指标和日志
- 严重等级: warning
- 来源: awesome-prometheus-alerts / Proxies, load balancers and service meshes / Istio
