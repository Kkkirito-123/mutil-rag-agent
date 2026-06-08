# Netdata MD mismatch cnt unsynchronized blocks

> Group: **Basic resource monitoring**  
> Service: **Netdata**  
> Exporter: `embedded-exporter`  
> Severity: **warning**  
> Duration (for): `2m`

## 现象 / Description

RAID Array have unsynchronized blocks

## PromQL 查询

```promql
netdata_md_mismatch_cnt_unsynchronized_blocks_average > 1024
```

## 故障定位

- 触发该告警时, 检查 Netdata 的相关指标和日志
- 严重等级: warning
- 来源: awesome-prometheus-alerts / Basic resource monitoring / Netdata
