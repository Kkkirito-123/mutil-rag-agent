# Flink all task slots used

> Group: **Data engineering**  
> Service: **Apache Flink**  
> Exporter: `flink-prometheus-reporter`  
> Severity: **warning**  
> Duration (for): `5m`

## 现象 / Description

All Flink task slots are in use ({{ $value }} available). New jobs cannot be scheduled.

## PromQL 查询

```promql
flink_jobmanager_taskSlotsAvailable == 0
```

## 处理建议 / Comments

This alert fires when there are no available task slots. Adjust the threshold if your cluster is expected to run at full capacity.

## 故障定位

- 触发该告警时, 检查 Apache Flink 的相关指标和日志
- 严重等级: warning
- 来源: awesome-prometheus-alerts / Data engineering / Apache Flink
