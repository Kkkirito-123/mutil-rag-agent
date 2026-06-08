# Blackbox configuration reload failure

> Group: **Basic resource monitoring**  
> Service: **Blackbox**  
> Exporter: `blackbox-exporter`  
> Severity: **warning**

## 现象 / Description

Blackbox configuration reload failure

## PromQL 查询

```promql
blackbox_exporter_config_last_reload_successful != 1
```

## 故障定位

- 触发该告警时, 检查 Blackbox 的相关指标和日志
- 严重等级: warning
- 来源: awesome-prometheus-alerts / Basic resource monitoring / Blackbox
