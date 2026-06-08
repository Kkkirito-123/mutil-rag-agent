# OpenStack exporter down

> Group: **Orchestrators**  
> Service: **OpenStack**  
> Exporter: `openstack-exporter`  
> Severity: **critical**  
> Duration (for): `2m`

## 现象 / Description

The OpenStack exporter is down. OpenStack cloud metrics are no longer being collected.

## PromQL 查询

```promql
up{job=~".*openstack.*"} == 0
```

## 处理建议 / Comments

Adjust the job label regex to match the actual job name in your Prometheus scrape config.

## 故障定位

- 触发该告警时, 检查 OpenStack 的相关指标和日志
- 严重等级: critical
- 来源: awesome-prometheus-alerts / Orchestrators / OpenStack
