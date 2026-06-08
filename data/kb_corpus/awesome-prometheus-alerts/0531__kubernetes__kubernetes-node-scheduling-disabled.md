# Kubernetes Node scheduling disabled

> Group: **Orchestrators**  
> Service: **Kubernetes**  
> Exporter: `kubestate-exporter`  
> Severity: **warning**  
> Duration (for): `30m`

## 现象 / Description

Node {{ $labels.node }} has been marked as unschedulable for more than 30 minutes.

## PromQL 查询

```promql
kube_node_spec_taint{key="node.kubernetes.io/unschedulable"} == 1
```

## 处理建议 / Comments

Kubernetes Node with disabled schedules are fine.
This alarm can be useful to get warned if there are nodes which are longer unscheduled.

## 故障定位

- 触发该告警时, 检查 Kubernetes 的相关指标和日志
- 严重等级: warning
- 来源: awesome-prometheus-alerts / Orchestrators / Kubernetes
