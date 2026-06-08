# SpeedTest Slow Internet Download

> Group: **Network and security**  
> Service: **SpeedTest**  
> Exporter: `nlamirault-speedtest-exporter`  
> Severity: **warning**

## 现象 / Description

Internet download speed is currently {{humanize $value}} Mbps.

## PromQL 查询

```promql
avg_over_time(speedtest_download[10m]) < 100
```

## 故障定位

- 触发该告警时, 检查 SpeedTest 的相关指标和日志
- 严重等级: warning
- 来源: awesome-prometheus-alerts / Network and security / SpeedTest
