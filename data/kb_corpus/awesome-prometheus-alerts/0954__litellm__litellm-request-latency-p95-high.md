# LiteLLM request latency p95 high

> Group: **Other**  
> Service: **LiteLLM**  
> Exporter: `embedded-exporter`  
> Severity: **warning**  
> Duration (for): `10m`

## 现象 / Description

LiteLLM request total latency p95 exceeds 10 seconds over 5min. Check downstream LLM provider response-times and proxy queue-depth.

## PromQL 查询

```promql
histogram_quantile(0.95, sum(rate(litellm_request_total_latency_metric_bucket[5m])) by (le)) > 10
```

## 故障定位

- 触发该告警时, 检查 LiteLLM 的相关指标和日志
- 严重等级: warning
- 来源: awesome-prometheus-alerts / Other / LiteLLM
