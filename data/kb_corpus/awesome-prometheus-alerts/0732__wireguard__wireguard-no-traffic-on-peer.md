# WireGuard no traffic on peer

> Group: **Network and security**  
> Service: **WireGuard**  
> Exporter: `mindflavor-prometheus-wireguard-exporter`  
> Severity: **warning**  
> Duration (for): `15m`

## 现象 / Description

WireGuard peer {{ $labels.public_key }} on interface {{ $labels.interface }} has had no traffic for 15 minutes despite an active handshake.

## PromQL 查询

```promql
(rate(wireguard_sent_bytes_total[15m]) + rate(wireguard_received_bytes_total[15m])) == 0 and wireguard_latest_handshake_seconds > 0 and (time() - wireguard_latest_handshake_seconds) < 300
```

## 处理建议 / Comments

This alert fires when a peer has a recent handshake but zero traffic flow.
May indicate routing issues or a misconfigured allowed-ips.
Only useful if you expect continuous traffic on all peers.

## 故障定位

- 触发该告警时, 检查 WireGuard 的相关指标和日志
- 严重等级: warning
- 来源: awesome-prometheus-alerts / Network and security / WireGuard
