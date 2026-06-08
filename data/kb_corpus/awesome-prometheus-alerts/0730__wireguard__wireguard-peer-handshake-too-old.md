# WireGuard peer handshake too old

> Group: **Network and security**  
> Service: **WireGuard**  
> Exporter: `mindflavor-prometheus-wireguard-exporter`  
> Severity: **warning**  
> Duration (for): `2m`

## 现象 / Description

WireGuard peer {{ $labels.public_key }} on interface {{ $labels.interface }} has not had a handshake for over 5 minutes. The tunnel may be down.

## PromQL 查询

```promql
time() - wireguard_latest_handshake_seconds > 300 and wireguard_latest_handshake_seconds > 0
```

## 处理建议 / Comments

The threshold of 300 seconds (5 minutes) is a rough default. WireGuard peers that are idle but reachable
typically re-handshake every 2 minutes. Adjust based on your keepalive interval.
The `> 0` guard excludes peers that have never completed a handshake (covered by a separate rule).

## 故障定位

- 触发该告警时, 检查 WireGuard 的相关指标和日志
- 严重等级: warning
- 来源: awesome-prometheus-alerts / Network and security / WireGuard
