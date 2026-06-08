# WireGuard peer handshake never established

> Group: **Network and security**  
> Service: **WireGuard**  
> Exporter: `mindflavor-prometheus-wireguard-exporter`  
> Severity: **critical**  
> Duration (for): `5m`

## 现象 / Description

WireGuard peer {{ $labels.public_key }} on interface {{ $labels.interface }} has never completed a handshake. Check peer configuration and network connectivity.

## PromQL 查询

```promql
wireguard_latest_handshake_seconds == 0
```

## 处理建议 / Comments

This alert will fire for all offline mobile/laptop peers. Consider filtering by expected-online peers.

## 故障定位

- 触发该告警时, 检查 WireGuard 的相关指标和日志
- 严重等级: critical
- 来源: awesome-prometheus-alerts / Network and security / WireGuard
