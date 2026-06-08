# Apache workers load

> Group: **Proxies, load balancers and service meshes**  
> Service: **Apache**  
> Exporter: `lusitaniae-apache-exporter`  
> Severity: **warning**  
> Duration (for): `2m`

## 现象 / Description

Apache workers in busy state approach the max workers count 80% workers busy on {{ $labels.instance }}

## PromQL 查询

```promql
(sum by (instance) (apache_workers{state="busy"}) / sum by (instance) (apache_scoreboard) ) * 100 > 80 and sum by (instance) (apache_scoreboard) > 0
```

## 故障定位

- 触发该告警时, 检查 Apache 的相关指标和日志
- 严重等级: warning
- 来源: awesome-prometheus-alerts / Proxies, load balancers and service meshes / Apache
