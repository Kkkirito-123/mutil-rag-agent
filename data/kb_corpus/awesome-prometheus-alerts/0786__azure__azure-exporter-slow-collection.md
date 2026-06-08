# Azure exporter slow collection

> Group: **Cloud providers**  
> Service: **Azure**  
> Exporter: `azure-metrics-exporter`  
> Severity: **warning**  
> Duration (for): `5m`

## 现象 / Description

Azure metrics exporter on {{ $labels.instance }} metric collection is taking more than 5 minutes ({{ $value }}s).

## PromQL 查询

```promql
azurerm_stats_metric_collecttime > 300
```

## 故障定位

- 触发该告警时, 检查 Azure 的相关指标和日志
- 严重等级: warning
- 来源: awesome-prometheus-alerts / Cloud providers / Azure
