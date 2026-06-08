# Container killed

> Group: **Basic resource monitoring**  
> Service: **Docker containers**  
> Exporter: `google-cadvisor`  
> Severity: **warning**

## 现象 / Description

A container has disappeared

## PromQL 查询

```promql
time() - container_last_seen > 60
```

## 处理建议 / Comments

This rule can be very noisy in dynamic infra with legitimate container start/stop/deployment.

## 故障定位

- 触发该告警时, 检查 Docker containers 的相关指标和日志
- 严重等级: warning
- 来源: awesome-prometheus-alerts / Basic resource monitoring / Docker containers
