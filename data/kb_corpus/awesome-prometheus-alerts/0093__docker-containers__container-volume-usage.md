# Container Volume usage

> Group: **Basic resource monitoring**  
> Service: **Docker containers**  
> Exporter: `google-cadvisor`  
> Severity: **warning**  
> Duration (for): `2m`

## 现象 / Description

Container Volume usage is above 80%

## PromQL 查询

```promql
(1 - (sum(container_fs_inodes_free{name!=""}) BY (instance) / sum(container_fs_inodes_total) BY (instance))) * 100 > 80 and sum(container_fs_inodes_total) BY (instance) > 0
```

## 故障定位

- 触发该告警时, 检查 Docker containers 的相关指标和日志
- 严重等级: warning
- 来源: awesome-prometheus-alerts / Basic resource monitoring / Docker containers
