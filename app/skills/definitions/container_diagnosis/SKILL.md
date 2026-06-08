---
name: container_diagnosis
display_name: Docker 容器诊断
description: 排查本机 Docker 容器异常 (容器挂了/重启循环/资源占用高/启动失败), 通过 docker CLI 真实查询容器状态、日志、配置
triggers:
  - 容器
  - docker
  - 镜像
  - container
  - milvus 挂了
  - 容器挂了
  - 容器起不来
  - 容器重启
  - 容器日志
  - docker ps
  - docker logs
allowed_tools:
  - search_knowledge_base
  - get_current_time
  - docker_ps
  - docker_stats
  - docker_logs
  - docker_inspect
  - docker_restart
  - web_search
risk_level: medium
---

# Docker 容器诊断 Playbook

## 适用场景
- 某个容器 (Milvus / Redis / MySQL / 自部署应用) 工作异常
- 容器频繁重启 (CrashLoopBackOff 类问题)
- 容器资源占用异常 (CPU 100% / 内存爆)
- 容器启动失败, 日志里有报错
- "我的 Milvus 是不是挂了"

## 不适用场景
- 集群级别 K8s/Swarm 编排问题 (本工具只查单机 Docker)
- 镜像仓库 / 镜像构建问题

## Phase 1: 摸底 (容器存在吗?)
1. 调 `docker_ps()` 看本机所有容器列表 + 状态
2. 在结果里找用户提到的容器名
3. 状态判断:
   - `Up X minutes/hours/days` → 在跑, 接 Phase 2
   - `Restarting (N) X seconds ago` → 重启循环, 直奔 Phase 3
   - `Exited (code) X minutes ago` → 已停止, 接 Phase 3
   - 没找到 → 容器名错了或从未创建

## Phase 2: 健康度 (在跑但表现差?)
1. 调 `docker_stats(name)` 看实时 CPU/MEM/IO
2. 阈值参考:
   - CPU > 90% 持续 → 容器内应用 CPU 密集 / 死循环
   - MEM 接近 limit → 即将 OOMKilled
   - 网络 IO 异常高 → 网络热点
3. 调 `docker_logs(name, tail=100)` 看最近日志:
   - 找 `ERROR` / `FATAL` / `panic` / `OOM` 关键字
   - 看时间戳是否密集 (高频报错)

## Phase 3: 死亡分析 (停止/重启循环)
1. 调 `docker_inspect(name)` 拿:
   - `State.ExitCode` — 退出码:
     - 0 = 正常退出 (但可能不是预期)
     - 137 = 被 SIGKILL (常见于 OOM)
     - 139 = 段错误
     - 1 / 2 = 应用主动 exit
   - `State.Error` — 错误信息
   - `RestartCount` — 重启次数
   - `HostConfig.RestartPolicy` — 重启策略
2. 调 `docker_logs(name, tail=200, since_minutes=10)` 看死前最后日志
3. 推断:
   - 退出码 137 + RestartCount 高 → OOM, 调大内存 limit
   - 日志里有应用业务报错 → 应用 bug
   - 日志里有 "config not found" / "permission denied" → 挂载配置问题
   - 启动后立刻退出 + 无错 → 命令配置错 (没有前台进程)

## Phase 4: 处置建议
- **OOM**: 调 `docker run --memory` limit 或排查容器内内存泄漏
- **配置错**: 看挂载卷 / 环境变量 / 启动命令
- **应用 bug**: 进入应用层排查 (转 generic_oncall + 日志)
- **临时止血**: 如果 `DOCKER_ALLOW_RESTART=true` 已配置, 可调 `docker_restart(name)` 拉起容器, 但**先看日志** 确认重启不会丢数据

## 注意事项
- **docker_restart 默认禁用** — 是写操作, 需 `.env` 显式开启 `DOCKER_ALLOW_RESTART=true`
- **不要 docker rm / docker rmi** — 工具未提供, 避免误删
- **生产环境慎重启** — 临时容器重启没事, 但有状态服务 (DB/Redis) 重启可能丢内存数据
- **日志超过 4000 字符会截断** — 太长就用 `since_minutes` 缩小范围
