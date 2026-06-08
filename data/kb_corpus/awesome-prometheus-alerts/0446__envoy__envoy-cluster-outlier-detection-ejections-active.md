# Envoy cluster outlier detection ejections active

> Group: **Proxies, load balancers and service meshes**  
> Service: **Envoy**  
> Exporter: `embedded-exporter`  
> Severity: **info**  
> Duration (for): `5m`

## 现象 / Description

There are active outlier detection ejections in cluster {{ $labels.envoy_cluster_name }} on {{ $labels.instance }}

## PromQL 查询

```promql
envoy_cluster_outlier_detection_ejections_active > 0
```

## 故障定位

- 触发该告警时, 检查 Envoy 的相关指标和日志
- 严重等级: info
- 来源: awesome-prometheus-alerts / Proxies, load balancers and service meshes / Envoy
