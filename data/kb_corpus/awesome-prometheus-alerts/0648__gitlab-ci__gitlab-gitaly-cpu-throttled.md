# GitLab Gitaly CPU throttled

> Group: **CI/CD**  
> Service: **GitLab CI**  
> Exporter: `gitaly`  
> Severity: **warning**  
> Duration (for): `5m`

## 现象 / Description

Gitaly processes on {{ $labels.instance }} are being CPU throttled by cgroups.

## PromQL 查询

```promql
rate(gitaly_cgroup_cpu_cfs_throttled_seconds_total[5m]) > 0.1
```

## 处理建议 / Comments

Brief throttling spikes are normal. Threshold of 0.1s/s (10% of CPU time throttled) filters out transient noise.

## 故障定位

- 触发该告警时, 检查 GitLab CI 的相关指标和日志
- 严重等级: warning
- 来源: awesome-prometheus-alerts / CI/CD / GitLab CI
