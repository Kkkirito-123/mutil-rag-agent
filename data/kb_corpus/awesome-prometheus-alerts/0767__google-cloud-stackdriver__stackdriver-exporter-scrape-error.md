# Stackdriver exporter scrape error

> Group: **Cloud providers**  
> Service: **Google Cloud Stackdriver**  
> Exporter: `stackdriver-exporter`  
> Severity: **warning**  
> Duration (for): `5m`

## 现象 / Description

Stackdriver exporter failed to scrape metrics from Google Cloud Monitoring API for project {{ $labels.project_id }}.

## PromQL 查询

```promql
stackdriver_monitoring_last_scrape_error > 0
```

## 故障定位

- 触发该告警时, 检查 Google Cloud Stackdriver 的相关指标和日志
- 严重等级: warning
- 来源: awesome-prometheus-alerts / Cloud providers / Google Cloud Stackdriver
