# Envoy listener SSL connection errors

> Group: **Proxies, load balancers and service meshes**  
> Service: **Envoy**  
> Exporter: `embedded-exporter`  
> Severity: **warning**

## 现象 / Description

Envoy listener is experiencing SSL/TLS connection errors on {{ $labels.instance }} ({{ $value }} in the last 5m)

## PromQL 查询

```promql
increase(envoy_listener_ssl_connection_error[5m]) > 5
```

## 故障定位

- 触发该告警时, 检查 Envoy 的相关指标和日志
- 严重等级: warning
- 来源: awesome-prometheus-alerts / Proxies, load balancers and service meshes / Envoy
