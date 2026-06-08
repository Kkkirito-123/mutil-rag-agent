# Keycloak high login failure rate

> Group: **Network and security**  
> Service: **Keycloak**  
> Exporter: `aerogear-keycloak-metrics-spi`  
> Severity: **warning**  
> Duration (for): `5m`

## 现象 / Description

More than 5% of login attempts are failing in realm {{ $labels.realm }} (current value: {{ $value | printf "%.1f" }}%).

## PromQL 查询

```promql
(sum by (realm) (rate(keycloak_failed_login_attempts_total[5m])) / (sum by (realm) (rate(keycloak_logins_total[5m])) + sum by (realm) (rate(keycloak_failed_login_attempts_total[5m])))) * 100 > 5 and (sum by (realm) (rate(keycloak_logins_total[5m])) + sum by (realm) (rate(keycloak_failed_login_attempts_total[5m]))) > 0
```

## 处理建议 / Comments

Threshold of 5% is a rough default. Adjust based on your user base and expected error rates.
A spike in failed logins may indicate a brute-force attack or misconfigured client.

## 故障定位

- 触发该告警时, 检查 Keycloak 的相关指标和日志
- 严重等级: warning
- 来源: awesome-prometheus-alerts / Network and security / Keycloak
