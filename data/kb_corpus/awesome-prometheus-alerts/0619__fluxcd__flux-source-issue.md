# Flux Source Issue

> Group: **CI/CD**  
> Service: **FluxCD**  
> Exporter: `embedded-exporter`  
> Severity: **warning**  
> Duration (for): `15m`

## 现象 / Description

Flux source {{ $labels.customresource_kind }} '{{ $labels.name }}' has issue(s).

## PromQL 查询

```promql
gotk_resource_info{ready="False", customresource_kind=~"GitRepository|HelmRepository|Bucket|OCIRepository"} > 0
```

## 故障定位

- 触发该告警时, 检查 FluxCD 的相关指标和日志
- 严重等级: warning
- 来源: awesome-prometheus-alerts / CI/CD / FluxCD
