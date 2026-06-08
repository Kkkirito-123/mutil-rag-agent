# OpenEBS used pool capacity

> Group: **Storage**  
> Service: **OpenEBS**  
> Exporter: `embedded-exporter`  
> Severity: **warning**  
> Duration (for): `2m`

## 现象 / Description

OpenEBS Pool use more than 80% of his capacity

## PromQL 查询

```promql
openebs_used_pool_capacity_percent > 80
```

## 故障定位

- 触发该告警时, 检查 OpenEBS 的相关指标和日志
- 严重等级: warning
- 来源: awesome-prometheus-alerts / Storage / OpenEBS
