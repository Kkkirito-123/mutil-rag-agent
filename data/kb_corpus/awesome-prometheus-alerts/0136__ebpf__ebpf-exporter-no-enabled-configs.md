# eBPF exporter no enabled configs

> Group: **Basic resource monitoring**  
> Service: **eBPF**  
> Exporter: `ebpf-exporter`  
> Severity: **warning**  
> Duration (for): `5m`

## 现象 / Description

eBPF exporter has no enabled configurations. No eBPF programs are being run. (instance {{ $labels.instance }})

## PromQL 查询

```promql
ebpf_exporter_enabled_configs == 0 or absent(ebpf_exporter_enabled_configs)
```

## 故障定位

- 触发该告警时, 检查 eBPF 的相关指标和日志
- 严重等级: warning
- 来源: awesome-prometheus-alerts / Basic resource monitoring / eBPF
