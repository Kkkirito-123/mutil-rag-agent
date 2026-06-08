# Prometheus timeseries cardinality

> Group: **Basic resource monitoring**  
> Service: **Prometheus self-monitoring**  
> Exporter: `embedded-exporter`  
> Severity: **warning**

## 现象 / Description

The "{{ $labels.name }}" timeseries cardinality is getting very high: {{ $value }}

## PromQL 查询

```promql
label_replace(count by(__name__) ({__name__=~".+"}), "name", "$1", "__name__", "(.+)") > 10000
```

## 故障定位

- 触发该告警时, 检查 Prometheus self-monitoring 的相关指标和日志
- 严重等级: warning
- 来源: awesome-prometheus-alerts / Basic resource monitoring / Prometheus self-monitoring
