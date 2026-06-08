# Azure API write rate limit approaching

> Group: **Cloud providers**  
> Service: **Azure**  
> Exporter: `azure-metrics-exporter`  
> Severity: **warning**

## 现象 / Description

Azure API write rate limit for subscription {{ $labels.subscriptionID }} is running low ({{ $value }} remaining).

## PromQL 查询

```promql
azurerm_api_ratelimit{type="write"} < 50
```

## 故障定位

- 触发该告警时, 检查 Azure 的相关指标和日志
- 严重等级: warning
- 来源: awesome-prometheus-alerts / Cloud providers / Azure
