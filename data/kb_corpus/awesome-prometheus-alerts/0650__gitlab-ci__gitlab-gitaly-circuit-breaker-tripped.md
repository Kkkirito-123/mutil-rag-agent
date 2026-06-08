# GitLab Gitaly circuit breaker tripped

> Group: **CI/CD**  
> Service: **GitLab CI**  
> Exporter: `gitaly`  
> Severity: **critical**

## 现象 / Description

Gitaly circuit breaker has tripped on {{ $labels.instance }}. Git operations are failing.

## PromQL 查询

```promql
increase(gitaly_circuit_breaker_transitions_total{to_state="open"}[5m]) > 0
```

## 处理建议 / Comments

When the circuit breaker trips to "open" state, Git operations (push, pull, clone) will fail.
Check Gitaly service health and logs.

## 故障定位

- 触发该告警时, 检查 GitLab CI 的相关指标和日志
- 严重等级: critical
- 来源: awesome-prometheus-alerts / CI/CD / GitLab CI
