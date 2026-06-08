# Linkerd high error rate

> Group: **Proxies, load balancers and service meshes**  
> Service: **Linkerd**  
> Exporter: `embedded-exporter`  
> Severity: **warning**  
> Duration (for): `1m`

## 现象 / Description

Linkerd error rate for {{ $labels.deployment }}{{ $labels.statefulset }}{{ $labels.daemonset }} is over 10%

## PromQL 查询

```promql
sum(rate(response_total{classification="failure"}[1m])) by (deployment, statefulset, daemonset) / sum(rate(response_total[1m])) by (deployment, statefulset, daemonset) * 100 > 10 and sum(rate(response_total[1m])) by (deployment, statefulset, daemonset) > 0
```

## 处理建议 / Comments

Linkerd does not expose request_errors_total. Errors are tracked via response_total{classification="failure"}.

## 故障定位

- 触发该告警时, 检查 Linkerd 的相关指标和日志
- 严重等级: warning
- 来源: awesome-prometheus-alerts / Proxies, load balancers and service meshes / Linkerd
