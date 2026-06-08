# AWS ALB unhealthy targets

> Group: **Cloud providers**  
> Service: **AWS CloudWatch**  
> Exporter: `prometheus-cloudwatch-exporter`  
> Severity: **critical**  
> Duration (for): `5m`

## 现象 / Description

ALB {{ $labels.load_balancer }} has {{ $value }} unhealthy target(s) in target group {{ $labels.target_group }}.

## PromQL 查询

```promql
aws_applicationelb_unhealthy_host_count_average > 0
```

## 处理建议 / Comments

Requires ApplicationELB UnHealthyHostCount metric.

## 故障定位

- 触发该告警时, 检查 AWS CloudWatch 的相关指标和日志
- 严重等级: critical
- 来源: awesome-prometheus-alerts / Cloud providers / AWS CloudWatch
