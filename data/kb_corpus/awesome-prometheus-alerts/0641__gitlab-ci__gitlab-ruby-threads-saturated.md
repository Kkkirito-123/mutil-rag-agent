# GitLab Ruby threads saturated

> Group: **CI/CD**  
> Service: **GitLab CI**  
> Exporter: `gitlab-built-in-exporter`  
> Severity: **warning**  
> Duration (for): `10m`

## 现象 / Description

GitLab running threads on {{ $labels.instance }} have exceeded the expected maximum ({{ $value }}).

## PromQL 查询

```promql
sum by (instance) (gitlab_ruby_threads_running_threads) > on(instance) gitlab_ruby_threads_max_expected_threads * 1.5
```

## 故障定位

- 触发该告警时, 检查 GitLab CI 的相关指标和日志
- 严重等级: warning
- 来源: awesome-prometheus-alerts / CI/CD / GitLab CI
