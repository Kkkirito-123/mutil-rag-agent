# LiteLLM proxy failed requests rate high

> Group: **Other**  
> Service: **LiteLLM**  
> Exporter: `embedded-exporter`  
> Severity: **warning**  
> Duration (for): `10m`

## 现象 / Description

LiteLLM proxy is returning failed responses to clients (>5% error rate over 5min). Investigate downstream LLM provider availability or auth issues.

## PromQL 查询

```promql
sum(rate(litellm_proxy_failed_requests_metric_total[5m])) / sum(rate(litellm_proxy_total_requests_metric_total[5m])) > 0.05
```

## 故障定位

- 触发该告警时, 检查 LiteLLM 的相关指标和日志
- 严重等级: warning
- 来源: awesome-prometheus-alerts / Other / LiteLLM
