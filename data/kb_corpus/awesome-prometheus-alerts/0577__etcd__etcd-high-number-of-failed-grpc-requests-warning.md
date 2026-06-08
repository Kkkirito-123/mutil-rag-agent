# Etcd high number of failed GRPC requests warning

> Group: **Orchestrators**  
> Service: **Etcd**  
> Exporter: `embedded-exporter`  
> Severity: **warning**  
> Duration (for): `2m`

## 现象 / Description

More than 1% GRPC request failure detected in Etcd

## PromQL 查询

```promql
sum(rate(grpc_server_handled_total{grpc_code=~"Internal|Unavailable|DeadlineExceeded|ResourceExhausted|Aborted|Unknown"}[1m])) BY (grpc_service, grpc_method) / sum(rate(grpc_server_handled_total[1m])) BY (grpc_service, grpc_method) > 0.01 and sum(rate(grpc_server_handled_total[1m])) BY (grpc_service, grpc_method) > 0
```

## 处理建议 / Comments

Filters to actual error codes. grpc_code!="OK" includes benign codes like NotFound, AlreadyExists, and Cancelled.

## 故障定位

- 触发该告警时, 检查 Etcd 的相关指标和日志
- 严重等级: warning
- 来源: awesome-prometheus-alerts / Orchestrators / Etcd
