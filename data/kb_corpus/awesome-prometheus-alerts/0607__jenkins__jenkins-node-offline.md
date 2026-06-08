# Jenkins node offline

> Group: **CI/CD**  
> Service: **Jenkins**  
> Exporter: `metric-plugin`  
> Severity: **critical**  
> Duration (for): `5m`

## 现象 / Description

At least one Jenkins node offline: `{{$labels.instance}}` in realm {{$labels.realm}}/{{$labels.env}} ({{$labels.region}})

## PromQL 查询

```promql
jenkins_node_offline_value > 0
```

## 故障定位

- 触发该告警时, 检查 Jenkins 的相关指标和日志
- 严重等级: critical
- 来源: awesome-prometheus-alerts / CI/CD / Jenkins
