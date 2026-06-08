# Host Network Bond Degraded

> Group: **Basic resource monitoring**  
> Service: **Host and hardware**  
> Exporter: `node-exporter`  
> Severity: **warning**  
> Duration (for): `2m`

## 现象 / Description

Bond "{{ $labels.device }}" degraded on "{{ $labels.instance }}".

## PromQL 查询

```promql
((node_bonding_active - node_bonding_slaves) != 0)
```

## 故障定位

- 触发该告警时, 检查 Host and hardware 的相关指标和日志
- 严重等级: warning
- 来源: awesome-prometheus-alerts / Basic resource monitoring / Host and hardware
