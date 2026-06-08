# Apache down

> Group: **Proxies, load balancers and service meshes**  
> Service: **Apache**  
> Exporter: `lusitaniae-apache-exporter`  
> Severity: **critical**

## 现象 / Description

Apache down

## PromQL 查询

```promql
apache_up == 0
```

## 故障定位

- 触发该告警时, 检查 Apache 的相关指标和日志
- 严重等级: critical
- 来源: awesome-prometheus-alerts / Proxies, load balancers and service meshes / Apache
