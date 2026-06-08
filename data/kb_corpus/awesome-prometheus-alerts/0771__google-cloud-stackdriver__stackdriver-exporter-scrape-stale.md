# Stackdriver exporter scrape stale

> Group: **Cloud providers**  
> Service: **Google Cloud Stackdriver**  
> Exporter: `stackdriver-exporter`  
> Severity: **warning**

## 现象 / Description

Stackdriver exporter has not successfully scraped metrics for project {{ $labels.project_id }} in the last 10 minutes.

## PromQL 查询

```promql
time() - stackdriver_monitoring_last_scrape_timestamp > 600
```

## 故障定位

- 触发该告警时, 检查 Google Cloud Stackdriver 的相关指标和日志
- 严重等级: warning
- 来源: awesome-prometheus-alerts / Cloud providers / Google Cloud Stackdriver
