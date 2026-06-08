# Istio Mixer Prometheus dispatches low

> Group: **Proxies, load balancers and service meshes**  
> Service: **Istio**  
> Exporter: `embedded-exporter`  
> Severity: **warning**  
> Duration (for): `1m`

## 现象 / Description

Number of Mixer dispatches to Prometheus is too low. Istio metrics might not be being exported properly.

## PromQL 查询

```promql
sum(rate(mixer_runtime_dispatches_total{adapter=~"prometheus"}[1m])) < 180
```

## 处理建议 / Comments

Mixer was deprecated in Istio 1.5 and removed in Istio 1.8+. This alert only applies to Istio < 1.8.

## 故障定位

- 触发该告警时, 检查 Istio 的相关指标和日志
- 严重等级: warning
- 来源: awesome-prometheus-alerts / Proxies, load balancers and service meshes / Istio
