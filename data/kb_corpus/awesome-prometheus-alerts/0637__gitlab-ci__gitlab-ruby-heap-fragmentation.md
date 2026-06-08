# GitLab Ruby heap fragmentation

> Group: **CI/CD**  
> Service: **GitLab CI**  
> Exporter: `gitlab-built-in-exporter`  
> Severity: **warning**  
> Duration (for): `15m`

## 现象 / Description

GitLab Ruby heap fragmentation on {{ $labels.instance }} is {{ $value }}. High fragmentation wastes memory.

## PromQL 查询

```promql
ruby_gc_stat_ext_heap_fragmentation{job=~".*gitlab.*"} > 0.5
```

## 处理建议 / Comments

Heap fragmentation above 50% means a significant amount of memory is wasted.
A Puma worker restart may help reclaim memory.

## 故障定位

- 触发该告警时, 检查 GitLab CI 的相关指标和日志
- 严重等级: warning
- 来源: awesome-prometheus-alerts / CI/CD / GitLab CI
