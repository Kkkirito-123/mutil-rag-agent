# Thanos Receive High Forward Request Failures

> Group: **Observability**  
> Service: **Thanos**  
> Exporter: `thanos-receiver`  
> Severity: **info**  
> Duration (for): `5m`

## 现象 / Description

Thanos Receive {{$labels.job}} is failing to forward {{$value | humanize}}% of requests.

## PromQL 查询

```promql
(sum by (job) (rate(thanos_receive_forward_requests_total{result="error"}[5m]))/  sum by (job) (rate(thanos_receive_forward_requests_total[5m]))) * 100 > 20 and sum by (job) (rate(thanos_receive_forward_requests_total[5m])) > 0
```

## 故障定位

- 触发该告警时, 检查 Thanos 的相关指标和日志
- 严重等级: info
- 来源: awesome-prometheus-alerts / Observability / Thanos
