---
name: generic_oncall
display_name: 通用 OnCall 兜底排查
description: 当问题无法归类到具体故障 Skill 时使用, 通用 SRE 思路 (RAIL 法则)
triggers:
  - 通用
  - 不确定
  - 排查
allowed_tools:
  - search_knowledge_base
  - get_current_time
  - get_local_system_overview
  - get_local_cpu_memory
  - get_local_disk_usage
  - list_top_processes
  - web_search
  - query_windows_event
  - ping_host
  - http_check
  - dns_lookup
  - check_port
  - docker_ps
  - docker_stats
  - docker_logs
  - docker_inspect
risk_level: low
---

# 通用 OnCall 兜底 Playbook

## 适用场景
- 用户描述较模糊, 无法明确归类到具体故障类型
- 同时涉及多个组件 (服务 + DB + 中间件) 的复合故障
- 没有专属 Skill 覆盖的场景

## 数据源选择 (重要)
判断用户是问"远程生产服务"还是"本机/自己的电脑":
- 涉及"我电脑/我笔记本/本机/这台机器/我的设备"或没有任何远程主机名 → **优先用本机系统工具** (`get_local_system_overview` / `get_local_cpu_memory` / `get_local_disk_usage` / `list_top_processes`), 这是真实数据
- 涉及网络目标 → 用 `ping_host` / `http_check` / `dns_lookup` / `check_port`
- 涉及 Docker 容器 → 用 `docker_ps` / `docker_stats` / `docker_logs` / `docker_inspect`
- **绝对禁止**: 用户问"我电脑"却编造远程监控/日志数据

## 排查思路 (RAIL 法则)
1. **R - Recent changes (近期变更)**: 从用户描述和知识库确认是否有发布、配置、容量变化
2. **A - Alerts (相关告警)**: 用当前 Skill 可见的真实工具查询 CPU/内存/磁盘/网络/容器状态
3. **I - Issues (业务影响)**: 根据错误现象、Top 进程、网络探测或容器日志判断影响范围
4. **L - Logs (日志深挖)**: 优先使用可见日志/事件工具, 找 ERROR/OOM/timeout/permission denied 等线索
5. **本地资料不够时再联网兜底**: `web_search` 最多 2 次, 只查公开技术资料
6. 综合现有信息给出诊断结论或下一步排查建议; 信息不足时诚实说明并建议人工介入

## 输出重点
- 现象与影响范围
- 已有的关键证据 (监控指标 / 日志 / 知识库 SOP)
- 当前最可能的方向 (即使是初步推断也要标记为"初步")
- 紧急止损建议 (优先回滚) + 进一步排查建议
- 信息不足时, 明确说明"需要补充哪些数据 / 建议人工介入"

## 注意事项
- 当不确定时, **优先回滚胜于查根因** (生产止损永远第一位)
- 不要在证据不足时强行下根因结论
- 任何写操作均不自主执行, 仅作建议
