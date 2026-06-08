# Consul missing master node

> Group: **Orchestrators**  
> Service: **Consul**  
> Exporter: `consul-exporter`  
> Severity: **critical**

## 现象 / Description

Numbers of consul raft peers should be 3, in order to preserve quorum.

## PromQL 查询

```promql
consul_raft_peers < 3
```

## 故障定位

- 触发该告警时, 检查 Consul 的相关指标和日志
- 严重等级: critical
- 来源: awesome-prometheus-alerts / Orchestrators / Consul
