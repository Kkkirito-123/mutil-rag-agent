# Kubernetes Node disk pressure

> Group: **Orchestrators**  
> Service: **Kubernetes**  
> Exporter: `kubestate-exporter`  
> Severity: **critical**  
> Duration (for): `2m`

## 现象 / Description

Node {{ $labels.node }} has DiskPressure condition

## PromQL 查询

```promql
kube_node_status_condition{condition="DiskPressure",status="true"} == 1
```

## 故障定位

- 触发该告警时, 检查 Kubernetes 的相关指标和日志
- 严重等级: critical
- 来源: awesome-prometheus-alerts / Orchestrators / Kubernetes
