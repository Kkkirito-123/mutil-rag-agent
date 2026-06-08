# Cilium agent high denied rate

> Group: **Network and security**  
> Service: **Cilium**  
> Exporter: `embedded-exporter`  
> Severity: **info**  
> Duration (for): `10m`

## 现象 / Description

Cilium agent {{ $labels.pod }} is dropping packets due to policy denial. Verify network policies are correct.

## PromQL 查询

```promql
sum(rate(cilium_drop_count_total{reason="Policy denied"}[1m])) by (pod) > 0
```

## 处理建议 / Comments

Policy denials may be expected behavior. Investigate only if unexpected traffic is being blocked.

## 故障定位

- 触发该告警时, 检查 Cilium 的相关指标和日志
- 严重等级: info
- 来源: awesome-prometheus-alerts / Network and security / Cilium
