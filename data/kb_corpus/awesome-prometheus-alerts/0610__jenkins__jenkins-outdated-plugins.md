# Jenkins outdated plugins

> Group: **CI/CD**  
> Service: **Jenkins**  
> Exporter: `metric-plugin`  
> Severity: **warning**  
> Duration (for): `1d`

## 现象 / Description

{{ $value }} plugins need update

## PromQL 查询

```promql
sum(jenkins_plugins_withUpdate) by (instance) > 3
```

## 故障定位

- 触发该告警时, 检查 Jenkins 的相关指标和日志
- 严重等级: warning
- 来源: awesome-prometheus-alerts / CI/CD / Jenkins
