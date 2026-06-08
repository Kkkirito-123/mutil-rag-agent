# ArgoCD service unhealthy

> Group: **CI/CD**  
> Service: **ArgoCD**  
> Exporter: `embedded-exporter`  
> Severity: **warning**  
> Duration (for): `15m`

## 现象 / Description

Service {{ $labels.name }} run by argo is currently not healthy.

## PromQL 查询

```promql
argocd_app_info{health_status!="Healthy"} != 0
```

## 故障定位

- 触发该告警时, 检查 ArgoCD 的相关指标和日志
- 严重等级: warning
- 来源: awesome-prometheus-alerts / CI/CD / ArgoCD
