# IPMI SEL almost full

> Group: **Basic resource monitoring**  
> Service: **IPMI**  
> Exporter: `ipmi-exporter`  
> Severity: **warning**  
> Duration (for): `5m`

## 现象 / Description

IPMI System Event Log on {{ $labels.instance }} has only {{ printf "%.0f" $value }} bytes free. Clear the SEL to prevent loss of new events.

## PromQL 查询

```promql
ipmi_sel_free_space_bytes < 512
```

## 处理建议 / Comments

SEL storage is typically very limited (e.g., 16KB). When full, new events may be dropped.

## 故障定位

- 触发该告警时, 检查 IPMI 的相关指标和日志
- 严重等级: warning
- 来源: awesome-prometheus-alerts / Basic resource monitoring / IPMI
