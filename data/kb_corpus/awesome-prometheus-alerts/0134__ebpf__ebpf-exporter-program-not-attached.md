# eBPF exporter program not attached

> Group: **Basic resource monitoring**  
> Service: **eBPF**  
> Exporter: `ebpf-exporter`  
> Severity: **warning**  
> Duration (for): `5m`

## 现象 / Description

eBPF program {{ $labels.id }} failed to attach. The program is not collecting data. (instance {{ $labels.instance }})

## PromQL 查询

```promql
ebpf_exporter_ebpf_program_attached == 0
```

## 处理建议 / Comments

The exporter uses loose attachment: if a program fails to load (missing BTF, kernel incompatibility), it sets this metric to 0 and continues running.

## 故障定位

- 触发该告警时, 检查 eBPF 的相关指标和日志
- 严重等级: warning
- 来源: awesome-prometheus-alerts / Basic resource monitoring / eBPF
