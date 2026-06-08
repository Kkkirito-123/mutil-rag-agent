# Container High Memory usage

> Group: **Basic resource monitoring**  
> Service: **Docker containers**  
> Exporter: `google-cadvisor`  
> Severity: **warning**  
> Duration (for): `2m`

## 现象 / Description

Container Memory usage is above 80%

## PromQL 查询

```promql
(sum(container_memory_working_set_bytes{name!=""}) BY (instance, name) / sum(container_spec_memory_limit_bytes > 0) BY (instance, name) * 100) > 80
```

## 处理建议 / Comments

See https://medium.com/faun/how-much-is-too-much-the-linux-oomkiller-and-used-memory-d32186f29c9d

## 故障定位

- 触发该告警时, 检查 Docker containers 的相关指标和日志
- 严重等级: warning
- 来源: awesome-prometheus-alerts / Basic resource monitoring / Docker containers
