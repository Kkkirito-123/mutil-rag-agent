# Hadoop Name Node Down

> Group: **Data engineering**  
> Service: **Hadoop**  
> Exporter: `jmx_exporter`  
> Severity: **critical**  
> Duration (for): `5m`

## 现象 / Description

The Hadoop NameNode service is unavailable.

## PromQL 查询

```promql
up{job="hadoop-namenode"} == 0
```

## 处理建议 / Comments

When targets are managed via service discovery, a disappeared target goes stale rather than reporting up==0,
so this alert may not fire. Prefer application-level availability metrics if available.
Rename job="hadoop-namenode" to match the actual job name in your Prometheus scrape config.

## 故障定位

- 触发该告警时, 检查 Hadoop 的相关指标和日志
- 严重等级: critical
- 来源: awesome-prometheus-alerts / Data engineering / Hadoop
