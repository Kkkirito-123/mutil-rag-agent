# Keycloak no successful logins

> Group: **Network and security**  
> Service: **Keycloak**  
> Exporter: `aerogear-keycloak-metrics-spi`  
> Severity: **critical**  
> Duration (for): `5m`

## 现象 / Description

No successful logins in realm {{ $labels.realm }} for the last 15 minutes.

## PromQL 查询

```promql
sum by (realm) (rate(keycloak_logins_total[15m])) == 0 and (sum by (realm) (rate(keycloak_logins_total[15m])) + sum by (realm) (rate(keycloak_failed_login_attempts_total[15m]))) > 0
```

## 处理建议 / Comments

Only fires when login attempts exist but none succeed — may indicate an authentication outage.

## 故障定位

- 触发该告警时, 检查 Keycloak 的相关指标和日志
- 严重等级: critical
- 来源: awesome-prometheus-alerts / Network and security / Keycloak
