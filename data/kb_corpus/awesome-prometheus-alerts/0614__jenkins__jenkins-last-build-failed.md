# Jenkins last build failed

> Group: **CI/CD**  
> Service: **Jenkins**  
> Exporter: `metric-plugin`  
> Severity: **warning**

## 现象 / Description

Last build failed: {{$labels.jenkins_job}}. Failed build for job `{{$labels.jenkins_job}}` on {{$labels.instance}}/{{$labels.env}} ({{$labels.region}})

## PromQL 查询

```promql
default_jenkins_builds_last_build_result_ordinal == 2
```

## 处理建议 / Comments

* RUNNING  -1 true  - The build had no errors.
* SUCCESS   0 true  - The build had no errors.
* UNSTABLE  1 true  - The build had some errors but they were not fatal. For example, some tests failed.
* FAILURE   2 false - The build had a fatal error.
* NOT_BUILT 3 false - The module was not built.
* ABORTED   4 false - The build was manually aborted.

## 故障定位

- 触发该告警时, 检查 Jenkins 的相关指标和日志
- 严重等级: warning
- 来源: awesome-prometheus-alerts / CI/CD / Jenkins
