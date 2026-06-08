---
name: host_resource_diagnosis
display_name: 主机资源诊断 (CPU/内存/磁盘)
description: 本机或主机 CPU 高、内存高/OOM、磁盘满、系统卡顿、风扇响等资源类故障。通过 psutil 真实采集后按现象分支 (CPU / 内存 / 磁盘)
triggers:
  # 本机词 (吸收原 local_machine_diagnosis)
  - 我的电脑
  - 我电脑
  - 我的笔记本
  - 我笔记本
  - 本机
  - 这台电脑
  - 这台机器
  - 自己的电脑
  - 我的机器
  - 本地电脑
  - 本地机器
  - localhost
  - my computer
  - my laptop
  - my pc
  # CPU 词 (吸收原 cpu_high_usage)
  - cpu 高
  - cpu 100
  - cpu 使用率
  - cpu 持续高
  - load average
  - 负载高
  - 主机变慢
  - 电脑卡
  - 风扇响
  # 内存词 (吸收原 memory_high_usage)
  - 内存高
  - 内存使用率
  - oom
  - oomkilled
  - memory leak
  - 内存泄漏
  - 内存满
  - 内存爆
  # 磁盘词 (吸收原 disk_full)
  - 磁盘满
  - 磁盘使用率
  - disk full
  - no space left
  - 磁盘告警
  - inode 满
  - 没空间
allowed_tools:
  - search_knowledge_base
  - get_current_time
  - get_local_system_overview
  - get_local_cpu_memory
  - get_local_disk_usage
  - list_top_processes
  - query_windows_event
  - web_search
risk_level: low
---

# 主机资源诊断 Playbook

## 适用场景
- 主机/容器 CPU 持续 >80% 或 load 异常
- 主机/容器内存 >85%、频繁 OOMKilled、进程 RSS 持续上涨疑似泄漏
- 磁盘使用率 >80%、inode 用尽、`No space left on device`
- 用户报告"我电脑/我笔记本/本机"卡顿、风扇响、崩溃、无空间等资源类问题
- 告警内容包含 cpu_high / load_high / memory_high / oom / disk_full / pod restart

**不适用**: 纯网络问题 (网址打不开/DNS 异常) 走 `network_diagnosis`; 容器级故障 (docker 容器挂了/重启循环) 走 `container_diagnosis`。

## 数据来源约束 (重要, 继承自原 local_machine_diagnosis)
- 工具数据全部来自本机 psutil 实时采集, **是真实的**, 不要写"模拟数据"
- 禁止编造工具未返回的内容 (例如不要凭空提到"日志显示 OOM"、"远程监控告警")
- 知识库 (`search_knowledge_base`) 仅作通用排查思路参考, **不能作为本机现状的证据**

## Phase 1: 先拍快照 (必做, 一次调用定方向)
1. 调 `get_local_system_overview` 拿到 CPU/内存/磁盘整体快照
2. 对照用户描述判断真正的告警维度:
   - CPU 高？走 Phase 2-A
   - 内存高 / OOM？走 Phase 2-B
   - 磁盘满 / inode 满？走 Phase 2-C
   - 用户描述模糊 ("电脑卡")？三项都看, 优先关注偏离阈值最远的那个

## Phase 2-A: CPU 分支
1. 调 `get_local_cpu_memory` 看 CPU 分核心、负载、内存压力
2. 调 `list_top_processes(sort_by=cpu)` 找出 CPU 占用最高的进程
3. 判断形态:
   - 稳态高 → 持续计算密集/死循环/IO wait
   - 瞬时尖峰 → 定时任务/批处理/GC
   - 多核均满 → 整体过载, 需扩容或限流
4. 必要时查 `query_windows_event` 看系统事件, 仅本地资料不足才 `web_search`

## Phase 2-B: 内存分支
1. 调 `get_local_cpu_memory` 看内存细节与 swap 使用
2. 调 `list_top_processes(sort_by=memory)` 找出主要占用进程
3. 判断形态:
   - 稳态高 → 缓存/常驻服务正常占用
   - 单调上涨 → 疑似内存泄漏 (需看趋势, 不能单点断定)
   - 伴随 OOMKilled → 容器 limit 过低或应用泄漏
4. 容器场景关注 cgroup 限制, 不要用宿主机数据误判

## Phase 2-C: 磁盘分支
1. 调 `get_local_disk_usage` 查看各分区使用率 + inode
2. 判断:
   - 空间用尽 → 找大文件占用源 (日志 / tmp / 临时文件)
   - inode 用尽 → 找大量小文件的目录 (空间可能才 50% 但 inode 已爆)
   - "幽灵文件" → 进程持有已删除文件 (`lsof | grep deleted`), 需 `truncate` 而非 `rm`

## Phase 3: 输出报告
**现状快照** (具体数值) + **问题判断** (真异常还是主观感受) + **最可能根因** (基于 Top 进程或分区数据) + **紧急止损建议** (限流/重启/扩容/清理) + **长期优化方向** (监控阈值/容量规划/代码优化/GC 调优/logrotate)。

报告必须写明:
- **数据来源**: "基于本机 psutil 实时采集" (不是 mock, 不是远程)
- **具体数值**: CPU %、内存 %、磁盘 % 不能省
- **诚实表态**: 数据不足时明确说明, 不强行下根因

## 注意事项
- 优先用真实监控数据, 不要凭空猜测
- 知识库 SOP 仅作思路参考, 不要直接照搬命令到生产
- 任何写操作 (kill / restart / 扩容 / 删文件) 必须建议人工确认, **不要自主执行**
- 不要 `rm` 正在被进程写入的文件, 空间不会释放, 应当 `truncate -s 0` 或重启进程
- 内存泄漏判断看 **趋势**, 单点高不一定是泄漏
