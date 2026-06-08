# CoreDNS Panic Count

> Group: **Network and security**  
> Service: **CoreDNS**  
> Exporter: `embedded-exporter`  
> Severity: **critical**

## 现象 / Description

Number of CoreDNS panics encountered

## PromQL 查询

```promql
increase(coredns_panics_total[1m]) > 0
```

## 故障定位

- 触发该告警时, 检查 CoreDNS 的相关指标和日志
- 严重等级: critical
- 来源: awesome-prometheus-alerts / Network and security / CoreDNS
