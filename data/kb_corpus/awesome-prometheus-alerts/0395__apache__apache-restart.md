# Apache restart

> Group: **Proxies, load balancers and service meshes**  
> Service: **Apache**  
> Exporter: `lusitaniae-apache-exporter`  
> Severity: **info**

## 现象 / Description

Apache has just been restarted.

## PromQL 查询

```promql
apache_uptime_seconds_total / 60 < 1
```

## 故障定位

- 触发该告警时, 检查 Apache 的相关指标和日志
- 严重等级: info
- 来源: awesome-prometheus-alerts / Proxies, load balancers and service meshes / Apache
