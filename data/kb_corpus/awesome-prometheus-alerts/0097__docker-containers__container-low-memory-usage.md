# Container Low Memory usage

> Group: **Basic resource monitoring**  
> Service: **Docker containers**  
> Exporter: `google-cadvisor`  
> Severity: **info**  
> Duration (for): `7d`

## 现象 / Description

Container Memory usage is under 20% for 1 week. Consider reducing the allocated memory.

## PromQL 查询

```promql
(sum(container_memory_working_set_bytes{name!=""}) BY (instance, name) / sum(container_spec_memory_limit_bytes > 0) BY (instance, name) * 100) < 20
```

## 故障定位

- 触发该告警时, 检查 Docker containers 的相关指标和日志
- 严重等级: info
- 来源: awesome-prometheus-alerts / Basic resource monitoring / Docker containers
