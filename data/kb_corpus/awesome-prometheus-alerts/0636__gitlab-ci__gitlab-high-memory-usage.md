# GitLab high memory usage

> Group: **CI/CD**  
> Service: **GitLab CI**  
> Exporter: `gitlab-built-in-exporter`  
> Severity: **warning**  
> Duration (for): `10m`

## 现象 / Description

GitLab process on {{ $labels.instance }} is using {{ $value | humanize1024 }}B of RSS memory.

## PromQL 查询

```promql
process_resident_memory_bytes{job=~".*gitlab.*"} > 2e+9
```

## 处理建议 / Comments

Threshold of 2GB may need adjustment based on your instance size.
High memory usage can lead to OOM kills and service disruptions.

## 故障定位

- 触发该告警时, 检查 GitLab CI 的相关指标和日志
- 严重等级: warning
- 来源: awesome-prometheus-alerts / CI/CD / GitLab CI
