# Freeswitch Sessions Warning

> Group: **Network and security**  
> Service: **Freeswitch**  
> Exporter: `znerol-freeswitch-exporter`  
> Severity: **warning**  
> Duration (for): `10m`

## 现象 / Description

High sessions usage on {{ $labels.instance }}: {{ $value | printf "%.2f"}}%

## PromQL 查询

```promql
(freeswitch_session_active * 100 / freeswitch_session_limit) > 80 and freeswitch_session_limit > 0
```

## 故障定位

- 触发该告警时, 检查 Freeswitch 的相关指标和日志
- 严重等级: warning
- 来源: awesome-prometheus-alerts / Network and security / Freeswitch
