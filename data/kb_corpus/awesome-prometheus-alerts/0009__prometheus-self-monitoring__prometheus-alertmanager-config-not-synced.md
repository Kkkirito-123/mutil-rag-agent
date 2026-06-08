# Prometheus AlertManager config not synced

> Group: **Basic resource monitoring**  
> Service: **Prometheus self-monitoring**  
> Exporter: `embedded-exporter`  
> Severity: **warning**

## 现象 / Description

Configurations of AlertManager cluster instances are out of sync

## PromQL 查询

```promql
count(count_values("config_hash", alertmanager_config_hash)) > 1
```

## 故障定位

- 触发该告警时, 检查 Prometheus self-monitoring 的相关指标和日志
- 严重等级: warning
- 来源: awesome-prometheus-alerts / Basic resource monitoring / Prometheus self-monitoring
