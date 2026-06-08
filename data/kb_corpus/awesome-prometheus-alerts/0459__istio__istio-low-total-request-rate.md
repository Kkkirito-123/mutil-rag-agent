# Istio low total request rate

> Group: **Proxies, load balancers and service meshes**  
> Service: **Istio**  
> Exporter: `embedded-exporter`  
> Severity: **warning**  
> Duration (for): `2m`

## 现象 / Description

Global request rate in the service mesh is unusually low ({{ $value | printf "%.2f" }} req/s).

## PromQL 查询

```promql
sum(rate(istio_requests_total{reporter="destination"}[5m])) < 100
```

## 处理建议 / Comments

Threshold of 100 req/s is a rough default. Adjust to your expected baseline traffic. This alert may fire on startup or low-traffic environments.

## 故障定位

- 触发该告警时, 检查 Istio 的相关指标和日志
- 严重等级: warning
- 来源: awesome-prometheus-alerts / Proxies, load balancers and service meshes / Istio
