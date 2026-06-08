# Cert-Manager absent

> Group: **Network and security**  
> Service: **cert-manager**  
> Exporter: `embedded-exporter`  
> Severity: **critical**  
> Duration (for): `10m`

## 现象 / Description

Cert-Manager has disappeared from Prometheus service discovery. New certificates will not be able to be minted, and existing ones can't be renewed until cert-manager is back.

## PromQL 查询

```promql
absent(up{job="cert-manager"})
```

## 故障定位

- 触发该告警时, 检查 cert-manager 的相关指标和日志
- 严重等级: critical
- 来源: awesome-prometheus-alerts / Network and security / cert-manager
