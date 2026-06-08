# Envoy SSL certificate expiring soon

> Group: **Proxies, load balancers and service meshes**  
> Service: **Envoy**  
> Exporter: `embedded-exporter`  
> Severity: **warning**

## 现象 / Description

SSL certificate loaded by Envoy on {{ $labels.instance }} expires in less than 7 days

## PromQL 查询

```promql
envoy_server_days_until_first_cert_expiring < 7
```

## 故障定位

- 触发该告警时, 检查 Envoy 的相关指标和日志
- 严重等级: warning
- 来源: awesome-prometheus-alerts / Proxies, load balancers and service meshes / Envoy
