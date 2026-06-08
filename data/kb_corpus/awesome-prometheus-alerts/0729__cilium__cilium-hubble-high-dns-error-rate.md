# Cilium Hubble high DNS error rate

> Group: **Network and security**  
> Service: **Cilium**  
> Exporter: `embedded-exporter`  
> Severity: **warning**  
> Duration (for): `5m`

## 现象 / Description

Cilium Hubble on {{ $labels.pod }} is observing more than 10% DNS error responses.

## PromQL 查询

```promql
sum(rate(hubble_dns_responses_total{rcode!="No Error"}[5m])) by (pod) / sum(rate(hubble_dns_responses_total[5m])) by (pod) > 0.1 and sum(rate(hubble_dns_responses_total[5m])) by (pod) > 0
```

## 处理建议 / Comments

Threshold of 10% is a rough default. Some DNS errors may be normal depending on your workload.

## 故障定位

- 触发该告警时, 检查 Cilium 的相关指标和日志
- 严重等级: warning
- 来源: awesome-prometheus-alerts / Network and security / Cilium
