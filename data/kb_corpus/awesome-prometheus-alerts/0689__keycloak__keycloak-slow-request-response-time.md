# Keycloak slow request response time

> Group: **Network and security**  
> Service: **Keycloak**  
> Exporter: `aerogear-keycloak-metrics-spi`  
> Severity: **warning**  
> Duration (for): `5m`

## 现象 / Description

Keycloak {{ $labels.method }} requests are taking more than 2 seconds on average.

## PromQL 查询

```promql
sum by (method) (rate(keycloak_request_duration_sum[5m])) / sum by (method) (rate(keycloak_request_duration_count[5m])) > 2000 and sum by (method) (rate(keycloak_request_duration_count[5m])) > 0
```

## 处理建议 / Comments

keycloak_request_duration is in milliseconds. Threshold of 2000ms (2 seconds) is a rough default.

## 故障定位

- 触发该告警时, 检查 Keycloak 的相关指标和日志
- 严重等级: warning
- 来源: awesome-prometheus-alerts / Network and security / Keycloak
