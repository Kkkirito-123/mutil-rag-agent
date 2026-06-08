# Stackdriver exporter high API calls

> Group: **Cloud providers**  
> Service: **Google Cloud Stackdriver**  
> Exporter: `stackdriver-exporter`  
> Severity: **warning**

## 现象 / Description

Stackdriver exporter is making {{ $value }} API calls per minute for project {{ $labels.project_id }}. This may hit Google Cloud Monitoring API quotas.

## PromQL 查询

```promql
rate(stackdriver_monitoring_api_calls_total[5m]) * 60 > 100
```

## 故障定位

- 触发该告警时, 检查 Google Cloud Stackdriver 的相关指标和日志
- 严重等级: warning
- 来源: awesome-prometheus-alerts / Cloud providers / Google Cloud Stackdriver
