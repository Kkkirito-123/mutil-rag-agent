---
name: network_diagnosis
display_name: 网络连通性诊断
description: 排查"网站打不开/接口超时/DNS 异常/端口不通"等网络问题, 使用 ping/HTTP/DNS/端口探测真实网络状态
triggers:
  - 网络
  - 网站打不开
  - 网址访问不了
  - 接口超时
  - 接口访问不了
  - "502"
  - "503"
  - "504"
  - 连不上
  - 连不通
  - dns
  - 域名解析
  - ping
  - 端口
  - 防火墙
  - 网速
allowed_tools:
  - search_knowledge_base
  - get_current_time
  - ping_host
  - http_check
  - dns_lookup
  - check_port
  - web_search
risk_level: low
---

# 网络连通性诊断 Playbook

## 适用场景
- 用户反馈"某网站打不开 / 接口访问不了"
- 接口返回 502/503/504 网关错误
- 应用报"connection refused / connection timeout"
- DNS 解析异常 (`nslookup` 报错或返回奇怪 IP)
- 怀疑端口被防火墙挡了

## 不适用场景
- 内网主机 (10.*/192.168.*/127.*) 的诊断 — 工具会拦截不允许扫描内网
- 性能调优 (带宽/丢包率深度分析)

## Phase 1: 信息收集
1. 从用户输入抽取**目标主机/URL/端口**, 没说清楚就直接问
2. 默认假设是公网地址 (域名或公网 IP), 内网工具会拒绝

## Phase 2: 分层排查 (从下往上)

### 第 1 层 — DNS 解析
- 调 `dns_lookup(domain)` 看域名能否解析到 IP
- 解析失败 → 大概率本机 DNS 配置问题或域名失效

### 第 2 层 — 网络连通性
- 调 `ping_host(host)` 看主机能否通达
- 不通 → 可能 ICMP 被禁 / 路由问题 / 主机宕机
- 通但延迟高 → 网络拥塞或跨地域

### 第 3 层 — 端口可达性
- 调 `check_port(host, port)` 验证目标端口
- 拒绝 → 服务未监听 (进程没起来)
- 超时 → 防火墙挡了 / 安全组没开

### 第 4 层 — 应用层
- 调 `http_check(url)` 发真实 HTTP 请求
- 关注**状态码** (5xx 是服务错误, 4xx 是客户端) + **响应时间** + **重定向链路**
- 也能看 `Server` 响应头判断对端 Web Server 类型

## Phase 3: 根因推断
按结果组合推断:

| DNS | Ping | Port | HTTP | 推断 |
|---|---|---|---|---|
| ❌ | - | - | - | DNS 配置错 / 域名失效 |
| ✅ | ❌ | - | - | 主机不通 / 路由问题 |
| ✅ | ✅ | ❌ | - | 端口未监听 / 防火墙挡 |
| ✅ | ✅ | ✅ | 5xx | 应用本身故障 |
| ✅ | ✅ | ✅ | 4xx | 请求姿势不对 / 鉴权问题 |
| ✅ | ✅ | ✅ | 2xx 慢 | 网络抖动或对端性能问题 |

## Phase 4: 处置建议
- DNS 失败: 切换 DNS (8.8.8.8 / 114.114.114.114), 清 DNS 缓存
- 主机不通: 联系网络组 / 看路由表
- 端口不通: 看安全组规则 / 服务进程是否启动
- HTTP 5xx: 进入应用层日志诊断 (转 generic_oncall)
- HTTP 慢: 看 CDN / 链路 / 对端负载

## 注意事项
- **拒绝扫描内网** — 工具内置黑名单, 不要绕过
- **不做主动攻击** — 不要批量扫 IP 段 / 暴力破密
- **限频** — 单次诊断 ping 不超过 10 次, http_check 不超过 3 个 URL
