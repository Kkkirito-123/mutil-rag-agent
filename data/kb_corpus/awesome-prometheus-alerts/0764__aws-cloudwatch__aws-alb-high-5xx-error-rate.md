# AWS ALB high 5xx error rate

> Group: **Cloud providers**  
> Service: **AWS CloudWatch**  
> Exporter: `prometheus-cloudwatch-exporter`  
> Severity: **critical**  
> Duration (for): `5m`

## 现象 / Description

ALB {{ $labels.load_balancer }} 5xx error rate is above 5% ({{ $value }}%).

## PromQL 查询

```promql
(aws_applicationelb_httpcode_elb_5_xx_count_sum / aws_applicationelb_request_count_sum) * 100 > 5 and aws_applicationelb_request_count_sum > 0
```

## 处理建议 / Comments

Requires ApplicationELB HTTPCode_ELB_5XX_Count and RequestCount metrics.

## 故障定位

- 触发该告警时, 检查 AWS CloudWatch 的相关指标和日志
- 严重等级: critical
- 来源: awesome-prometheus-alerts / Cloud providers / AWS CloudWatch
