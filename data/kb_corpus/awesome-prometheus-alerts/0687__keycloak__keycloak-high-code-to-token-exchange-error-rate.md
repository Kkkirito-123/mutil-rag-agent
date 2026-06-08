# Keycloak high code-to-token exchange error rate

> Group: **Network and security**  
> Service: **Keycloak**  
> Exporter: `aerogear-keycloak-metrics-spi`  
> Severity: **warning**  
> Duration (for): `5m`

## 现象 / Description

More than 10% of code-to-token exchanges are failing in realm {{ $labels.realm }} (current value: {{ $value | printf "%.1f" }}%).

## PromQL 查询

```promql
(sum by (realm) (rate(keycloak_code_to_tokens_errors_total[5m])) / sum by (realm) (rate(keycloak_code_to_tokens_total[5m]))) * 100 > 10 and sum by (realm) (rate(keycloak_code_to_tokens_total[5m])) > 0
```

## 处理建议 / Comments

Threshold of 10% is a rough default. Code-to-token failures may indicate misconfigured OAuth clients or replay attacks.

## 故障定位

- 触发该告警时, 检查 Keycloak 的相关指标和日志
- 严重等级: warning
- 来源: awesome-prometheus-alerts / Network and security / Keycloak
