# JVM memory filling up

> Group: **Runtimes**  
> Service: **JVM**  
> Exporter: `jvm-exporter`  
> Severity: **warning**  
> Duration (for): `2m`

## 现象 / Description

JVM memory is filling up (> 80%)

## PromQL 查询

```promql
(sum by (instance)(jvm_memory_used_bytes{area="heap"}) / sum by (instance)(jvm_memory_max_bytes{area="heap"})) * 100 > 80 and sum by (instance)(jvm_memory_max_bytes{area="heap"}) > 0
```

## 故障定位

- 触发该告警时, 检查 JVM 的相关指标和日志
- 严重等级: warning
- 来源: awesome-prometheus-alerts / Runtimes / JVM
