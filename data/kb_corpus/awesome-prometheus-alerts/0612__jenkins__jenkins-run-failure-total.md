# Jenkins run failure total

> Group: **CI/CD**  
> Service: **Jenkins**  
> Exporter: `metric-plugin`  
> Severity: **warning**

## 现象 / Description

Job run failures: ({{$value}}) {{$labels.jenkins_job}}. Healthcheck failure for `{{$labels.instance}}` in realm {{$labels.realm}}/{{$labels.env}} ({{$labels.region}})

## PromQL 查询

```promql
increase(jenkins_runs_failure_total[1h]) > 100
```

## 故障定位

- 触发该告警时, 检查 Jenkins 的相关指标和日志
- 严重等级: warning
- 来源: awesome-prometheus-alerts / CI/CD / Jenkins
