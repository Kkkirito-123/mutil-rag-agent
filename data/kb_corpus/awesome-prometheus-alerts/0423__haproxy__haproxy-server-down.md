# HAProxy server down

> Group: **Proxies, load balancers and service meshes**  
> Service: **HaProxy**  
> Exporter: `haproxy-exporter-v1`  
> Severity: **critical**

## 现象 / Description

HAProxy server is down

## PromQL 查询

```promql
haproxy_server_up == 0
```

## 故障定位

- 触发该告警时, 检查 HaProxy 的相关指标和日志
- 严重等级: critical
- 来源: awesome-prometheus-alerts / Proxies, load balancers and service meshes / HaProxy
