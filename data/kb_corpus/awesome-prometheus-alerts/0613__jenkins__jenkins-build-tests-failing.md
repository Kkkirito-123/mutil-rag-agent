# Jenkins build tests failing

> Group: **CI/CD**  
> Service: **Jenkins**  
> Exporter: `metric-plugin`  
> Severity: **warning**

## 现象 / Description

Last build tests failed: {{$labels.jenkins_job}}. Failed build Tests for job `{{$labels.jenkins_job}}` on {{$labels.instance}}/{{$labels.env}} ({{$labels.region}})

## PromQL 查询

```promql
default_jenkins_builds_last_build_tests_failing > 0
```

## 故障定位

- 触发该告警时, 检查 Jenkins 的相关指标和日志
- 严重等级: warning
- 来源: awesome-prometheus-alerts / CI/CD / Jenkins
