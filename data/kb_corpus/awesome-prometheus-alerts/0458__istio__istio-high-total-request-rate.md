# Istio high total request rate

> Group: **Proxies, load balancers and service meshes**  
> Service: **Istio**  
> Exporter: `embedded-exporter`  
> Severity: **warning**  
> Duration (for): `2m`

## 现象 / Description

Global request rate in the service mesh is unusually high ({{ $value | printf "%.2f" }} req/s).

## PromQL 查询

```promql
sum(rate(istio_requests_total{reporter="destination"}[5m])) > 1000
```

## 处理建议 / Comments

Threshold of 1000 req/s is a rough default. Adjust to your expected peak traffic.

## 故障定位

- 触发该告警时, 检查 Istio 的相关指标和日志
- 严重等级: warning
- 来源: awesome-prometheus-alerts / Proxies, load balancers and service meshes / Istio
