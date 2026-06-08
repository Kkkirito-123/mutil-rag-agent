# Azure exporter request errors

> Group: **Cloud providers**  
> Service: **Azure**  
> Exporter: `azure-metrics-exporter`  
> Severity: **warning**

## 现象 / Description

Azure metrics exporter on {{ $labels.instance }} has {{ $value }} API request errors in the last 15 minutes.

## PromQL 查询

```promql
increase(azurerm_stats_metric_requests{result="error"}[15m]) > 5
```

## 故障定位

- 触发该告警时, 检查 Azure 的相关指标和日志
- 严重等级: warning
- 来源: awesome-prometheus-alerts / Cloud providers / Azure
