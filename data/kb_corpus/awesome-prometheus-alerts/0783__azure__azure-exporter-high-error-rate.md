# Azure exporter high error rate

> Group: **Cloud providers**  
> Service: **Azure**  
> Exporter: `azure-metrics-exporter`  
> Severity: **warning**  
> Duration (for): `5m`

## 现象 / Description

Azure metrics exporter on {{ $labels.instance }} has an error rate above 10% ({{ $value }}%).

## PromQL 查询

```promql
sum by (instance) (rate(azurerm_stats_metric_requests{result="error"}[5m])) / sum by (instance) (rate(azurerm_stats_metric_requests[5m])) * 100 > 10 and sum by (instance) (rate(azurerm_stats_metric_requests[5m])) > 0
```

## 故障定位

- 触发该告警时, 检查 Azure 的相关指标和日志
- 严重等级: warning
- 来源: awesome-prometheus-alerts / Cloud providers / Azure
