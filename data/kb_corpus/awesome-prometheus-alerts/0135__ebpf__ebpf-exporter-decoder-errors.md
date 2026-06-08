# eBPF exporter decoder errors

> Group: **Basic resource monitoring**  
> Service: **eBPF**  
> Exporter: `ebpf-exporter`  
> Severity: **warning**  
> Duration (for): `5m`

## 现象 / Description

eBPF exporter is experiencing decoder errors for config {{ $labels.config }}. Kernel data is not being correctly transformed into labels. (instance {{ $labels.instance }})

## PromQL 查询

```promql
rate(ebpf_exporter_decoder_errors_total[5m]) > 0.05
```

## 故障定位

- 触发该告警时, 检查 eBPF 的相关指标和日志
- 严重等级: warning
- 来源: awesome-prometheus-alerts / Basic resource monitoring / eBPF
