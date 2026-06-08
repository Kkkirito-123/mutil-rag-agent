# JVM non-heap memory filling up

> Group: **Runtimes**  
> Service: **JVM**  
> Exporter: `jvm-exporter`  
> Severity: **warning**  
> Duration (for): `2m`

## 现象 / Description

JVM non-heap memory (metaspace/code cache) is filling up (> 80%)

## PromQL 查询

```promql
(sum by (instance)(jvm_memory_used_bytes{area="nonheap"}) / (sum by (instance)(jvm_memory_max_bytes{area="nonheap"}) > 0)) * 100 > 80
```

## 处理建议 / Comments

Many JVM configurations leave metaspace unbounded, in which case jvm_memory_max_bytes{area="nonheap"} is -1 and this alert will not fire.
The query filters out max_bytes <= 0 to avoid false negatives.

## 故障定位

- 触发该告警时, 检查 JVM 的相关指标和日志
- 严重等级: warning
- 来源: awesome-prometheus-alerts / Runtimes / JVM
