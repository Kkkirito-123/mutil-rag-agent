# Jenkins healthcheck

> Group: **CI/CD**  
> Service: **Jenkins**  
> Exporter: `metric-plugin`  
> Severity: **critical**

## 现象 / Description

Jenkins healthcheck score: {{$value}}. Healthcheck failure for `{{$labels.instance}}` in realm {{$labels.realm}}/{{$labels.env}} ({{$labels.region}})

## PromQL 查询

```promql
jenkins_health_check_score < 1
```

## 故障定位

- 触发该告警时, 检查 Jenkins 的相关指标和日志
- 严重等级: critical
- 来源: awesome-prometheus-alerts / CI/CD / Jenkins
