# PHP-FPM max-children reached

> Group: **Runtimes**  
> Service: **PHP-FPM**  
> Exporter: `bakins-fpm-exporter`  
> Severity: **warning**

## 现象 / Description

PHP-FPM reached max children on {{ $labels.instance }} ({{ $value }} times in the last 5m)

## PromQL 查询

```promql
sum(increase(phpfpm_max_children_reached_total[5m])) by (instance) > 3
```

## 故障定位

- 触发该告警时, 检查 PHP-FPM 的相关指标和日志
- 严重等级: warning
- 来源: awesome-prometheus-alerts / Runtimes / PHP-FPM
