# LiteLLM provider spend over budget

> Group: **Other**  
> Service: **LiteLLM**  
> Exporter: `embedded-exporter`  
> Severity: **warning**  
> Duration (for): `5m`

## 现象 / Description

Cumulative spend for an LLM provider has exceeded the daily budget threshold. Replace the regex `(claude-|anthropic/).*` with your provider's model-name pattern. Useful as a soft-warning when `provider_budget_config` hard-cap is unavailable or disabled.

## PromQL 查询

```promql
sum(increase(litellm_spend_metric_total{model=~"(claude-|anthropic/).*"}[24h])) > 1
```

## 处理建议 / Comments

The threshold (1) is in USD. The `model` label carries the resolved model-name (post-routing). 
PromQL `increase()` requires ≥2 datapoints with growth-difference to extrapolate positive — 
for brand-new counter series this needs ≥2 distinct request bursts ≥1 scrape-cycle apart.

## 故障定位

- 触发该告警时, 检查 LiteLLM 的相关指标和日志
- 严重等级: warning
- 来源: awesome-prometheus-alerts / Other / LiteLLM
