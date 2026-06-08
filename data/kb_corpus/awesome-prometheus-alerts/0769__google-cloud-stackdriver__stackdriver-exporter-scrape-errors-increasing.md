# Stackdriver exporter scrape errors increasing

> Group: **Cloud providers**  
> Service: **Google Cloud Stackdriver**  
> Exporter: `stackdriver-exporter`  
> Severity: **warning**

## 现象 / Description

Stackdriver exporter has had {{ $value }} scrape errors in the last 15 minutes for project {{ $labels.project_id }}.

## PromQL 查询

```promql
increase(stackdriver_monitoring_scrape_errors_total[15m]) > 5
```

## 故障定位

- 触发该告警时, 检查 Google Cloud Stackdriver 的相关指标和日志
- 严重等级: warning
- 来源: awesome-prometheus-alerts / Cloud providers / Google Cloud Stackdriver
