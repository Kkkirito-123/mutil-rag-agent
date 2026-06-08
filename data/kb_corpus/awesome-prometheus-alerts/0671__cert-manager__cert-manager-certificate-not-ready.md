# Cert-Manager certificate not ready

> Group: **Network and security**  
> Service: **cert-manager**  
> Exporter: `embedded-exporter`  
> Severity: **critical**  
> Duration (for): `10m`

## 现象 / Description

The certificate {{ $labels.name }} in namespace {{ $labels.exported_namespace }} is not ready to serve traffic.

## PromQL 查询

```promql
max by (name, exported_namespace, namespace, condition) (certmanager_certificate_ready_status{condition!="True"} == 1)
```

## 故障定位

- 触发该告警时, 检查 cert-manager 的相关指标和日志
- 严重等级: critical
- 来源: awesome-prometheus-alerts / Network and security / cert-manager
