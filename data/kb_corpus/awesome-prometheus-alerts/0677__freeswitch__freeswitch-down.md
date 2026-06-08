# Freeswitch down

> Group: **Network and security**  
> Service: **Freeswitch**  
> Exporter: `znerol-freeswitch-exporter`  
> Severity: **critical**  
> Duration (for): `1m`

## 现象 / Description

Freeswitch {{ $labels.instance }} is unresponsive.

## PromQL 查询

```promql
freeswitch_up == 0
```

## 故障定位

- 触发该告警时, 检查 Freeswitch 的相关指标和日志
- 严重等级: critical
- 来源: awesome-prometheus-alerts / Network and security / Freeswitch
