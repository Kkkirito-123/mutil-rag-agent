# Istio Pilot high push error rate

> Group: **Proxies, load balancers and service meshes**  
> Service: **Istio**  
> Exporter: `embedded-exporter`  
> Severity: **warning**  
> Duration (for): `1m`

## 现象 / Description

Number of Istio Pilot push errors is too high (> 5%). Envoy sidecars might have outdated configuration.

## PromQL 查询

```promql
sum(rate(pilot_xds_push_errors[1m])) / sum(rate(pilot_xds_pushes[1m])) * 100 > 5 and sum(rate(pilot_xds_pushes[1m])) > 0
```

## 故障定位

- 触发该告警时, 检查 Istio 的相关指标和日志
- 严重等级: warning
- 来源: awesome-prometheus-alerts / Proxies, load balancers and service meshes / Istio
