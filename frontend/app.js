// ============================================================
// Multi-Agent AIOps Platform - Frontend Logic
// ============================================================

const API = "/api/v1";

// ---------- Tab 切换 ----------
document.querySelectorAll(".tab-btn").forEach((btn) => {
    btn.addEventListener("click", () => {
        document.querySelectorAll(".tab-btn").forEach((b) => b.classList.remove("tab-active"));
        document.querySelectorAll(".tab-pane").forEach((p) => p.classList.add("hidden"));
        btn.classList.add("tab-active");
        const tab = btn.dataset.tab;
        document.getElementById(`tab-${tab}`).classList.remove("hidden");
        if (tab === "documents") {
            loadDocs();
            if (typeof loadEvalReports === "function") loadEvalReports();
        }
        if (tab === "incidents") incOnTabEnter();
        else incOnTabLeave();
        if (tab === "wiki" && typeof wikiOnTabEnter === "function") wikiOnTabEnter();
    });
});

// ---------- 健康检查 ----------
async function checkHealth() {
    try {
        const r = await fetch(`${API}/health/ready`);
        const data = await r.json();
        const ready = data?.data?.status === "ready";
        const milvusOk = data?.data?.dependencies?.milvus?.status === "ok";
        const mcpOk = data?.data?.dependencies?.mcp?.status === "ok";
        const dot = document.getElementById("health-dot");
        const text = document.getElementById("health-text");
        if (ready && mcpOk) {
            dot.className = "status-dot is-success";
            text.textContent = `就绪 · MCP ${data.data.dependencies.mcp.tools_count} 工具`;
        } else if (ready) {
            dot.className = "status-dot is-pending";
            text.textContent = "就绪 · MCP 未连";
        } else {
            dot.className = "status-dot is-failed";
            text.textContent = "Milvus 不可用";
        }
    } catch (e) {
        document.getElementById("health-text").textContent = "服务不可达";
    }
}
checkHealth();
setInterval(checkHealth, 15000);

// ============================================================
// Skill 列表 (页面加载时拉一次, 后续诊断时高亮选中项)
// ============================================================
// 风险等级用克制的 severity 圆点表达, 而不是整卡 pastel 撞色 (与全站"圆点+单色"语言一致)
const RISK_BADGE = {
    low:    { sev: "sev-info",     label: "低风险" },
    medium: { sev: "sev-warning",  label: "中风险" },
    high:   { sev: "sev-critical", label: "高风险" },
};

async function loadSkills() {
    const listEl = document.getElementById("skill-list");
    const countEl = document.getElementById("skill-count");
    try {
        const r = await fetch(`${API}/skills`);
        const data = await r.json();
        if (data?.code !== "SUCCESS") throw new Error(data?.message || "加载 Skill 失败");
        const skills = data?.data?.skills || [];
        countEl.textContent = `· ${skills.length} 个`;

        if (skills.length === 0) {
            listEl.innerHTML = '<span class="text-slate-400 italic col-span-full">暂无 Skill 注册</span>';
            return;
        }

        listEl.innerHTML = "";
        skills.forEach((s) => {
            const badge = RISK_BADGE[s.risk_level] || RISK_BADGE.low;
            const card = document.createElement("div");
            card.className = "skill-card border p-2";
            card.dataset.skillName = s.name;
            // tooltip 用 title (浏览器原生)
            card.title = `${s.display_name || s.name} · ${badge.label}`;
            card.innerHTML = `
                <div class="font-semibold truncate flex items-center"><span class="sev-dot ${badge.sev}"></span>${escapeHtml(s.display_name)}</div>
                <div class="text-[10px] opacity-70 font-mono truncate">${escapeHtml(s.name)}</div>
            `;
            listEl.appendChild(card);
        });
    } catch (e) {
        listEl.innerHTML = `<span class="text-red-500 col-span-full">加载失败: ${escapeHtml(e.message)}</span>`;
    }
}
loadSkills();

function highlightSkill(skillName, reason) {
    // 清除旧的高亮
    document.querySelectorAll(".skill-card.skill-active").forEach((el) => el.classList.remove("skill-active"));

    const card = document.querySelector(`.skill-card[data-skill-name="${CSS.escape(skillName || "")}"]`);
    const banner = document.getElementById("skill-selected-banner");
    const nameEl = document.getElementById("skill-selected-name");
    const reasonEl = document.getElementById("skill-reason");

    if (card) {
        card.classList.add("skill-active");
        card.scrollIntoView({ behavior: "smooth", block: "nearest", inline: "nearest" });
        nameEl.textContent = card.querySelector(".font-semibold")?.textContent || skillName;
    } else {
        nameEl.textContent = skillName || "(未知)";
    }
    banner.classList.remove("hidden");

    reasonEl.textContent = "";
    reasonEl.classList.add("hidden");
}

function clearSkillHighlight() {
    document.querySelectorAll(".skill-card.skill-active").forEach((el) => el.classList.remove("skill-active"));
    document.getElementById("skill-selected-banner").classList.add("hidden");
    document.getElementById("skill-reason").classList.add("hidden");
}

// ============================================================
// AIOps 诊断
// ============================================================
let aiopsAbortController = null;   // 实时模式: SSE 中止器
let aiopsPollTimer = null;         // 排队模式: 状态轮询定时器
let aiopsActiveTaskId = null;      // 排队模式: 当前跟踪的 task_id
const aiopsDiagnosisModeButtons = document.querySelectorAll("[data-aiops-diagnosis-mode]");
const aiopsSubmitModeButtons = document.querySelectorAll("[data-aiops-submit-mode]");
let aiopsDiagnosisMode = "fast";       // fast | deep
let aiopsSubmitMode = "realtime";      // realtime(同步 SSE) | queue(提交排队)

document.getElementById("aiops-start").addEventListener("click", startAiops);
document.getElementById("aiops-stop").addEventListener("click", () => {
    if (aiopsAbortController) aiopsAbortController.abort();   // 实时: 断开 SSE
    aiopsStopPolling();                                       // 排队: 停止跟踪 (后台任务仍会被 Worker 跑完)
    setAiopsRunning(false);
    document.getElementById("aiops-status").textContent = "已停止";
});

// 开始/停止按钮的 disabled 状态集中管理, 实时与排队两条路径共用
function setAiopsRunning(running) {
    document.getElementById("aiops-start").disabled = running;
    document.getElementById("aiops-stop").disabled = !running;
}

function aiopsStopPolling() {
    if (aiopsPollTimer) { clearTimeout(aiopsPollTimer); aiopsPollTimer = null; }
    aiopsActiveTaskId = null;
}

// 通用的"分段开关"渲染: 诊断模式 / 提交方式 共用 .diagnosis-mode-btn 视觉
function bindSegmentToggle(buttons, attr, getCur, setCur) {
    const render = () => buttons.forEach((btn) => {
        const active = btn.dataset[attr] === getCur();
        btn.classList.toggle("active", active);
        btn.setAttribute("aria-pressed", active ? "true" : "false");
    });
    buttons.forEach((btn) => btn.addEventListener("click", () => {
        setCur(btn.dataset[attr]);
        render();
    }));
    render();
}

bindSegmentToggle(aiopsDiagnosisModeButtons, "aiopsDiagnosisMode",
    () => aiopsDiagnosisMode, (v) => { aiopsDiagnosisMode = v || "fast"; });
bindSegmentToggle(aiopsSubmitModeButtons, "aiopsSubmitMode",
    () => aiopsSubmitMode, (v) => { aiopsSubmitMode = v || "realtime"; });

// 监控面板状态
const aiopsMonitor = {
    startTs: 0,
    timer: null,
    toolCount: 0,
    toolFail: 0,
    tokenCount: 0,           // 字符流粗估 (流过来即累加)
    realInputTokens: 0,      // LLM usage 真实 input
    realOutputTokens: 0,     // LLM usage 真实 output
    realTotalTokens: 0,
    cacheHitTokens: 0,       // DeepSeek 才有
    cacheMissTokens: 0,
    hasRealUsage: false,
    reset() {
        this.startTs = Date.now();
        this.toolCount = 0;
        this.toolFail = 0;
        this.tokenCount = 0;
        this.realInputTokens = 0;
        this.realOutputTokens = 0;
        this.realTotalTokens = 0;
        this.cacheHitTokens = 0;
        this.cacheMissTokens = 0;
        this.hasRealUsage = false;
        setText("mon-step", "—");
        setText("mon-step-label", "Skill Router 工作中...");
        setText("mon-elapsed", "0.0s");
        setText("mon-tools", "0");
        setText("mon-tools-fail", "失败 0");
        setText("mon-tokens", "0");
        setText("mon-tokens-detail", "输入 0 · 输出 0");
        setText("mon-tokens-badge", "~估算");
        setText("mon-stream-hint", "等待中");
        document.getElementById("mon-stream").innerHTML =
            '<span class="text-slate-400 italic">诊断开始后, 模型生成的文本会实时显示在此...</span>';
        document.getElementById("mon-tool-feed").innerHTML =
            '<span class="text-slate-400 italic px-2">暂无工具调用</span>';
        if (this.timer) clearInterval(this.timer);
        this.timer = setInterval(() => {
            const s = ((Date.now() - this.startTs) / 1000).toFixed(1);
            setText("mon-elapsed", `${s}s`);
        }, 100);
    },
    stop() {
        if (this.timer) {
            clearInterval(this.timer);
            this.timer = null;
        }
    },
};

function setText(id, v) {
    const el = document.getElementById(id);
    if (el) el.textContent = v;
}

function showAiopsReport() {
    document.getElementById("aiops-monitor").classList.add("hidden");
    const rep = document.getElementById("aiops-report");
    rep.classList.remove("hidden");
    setText("aiops-right-title", "诊断报告");
}

function showAiopsMonitor() {
    document.getElementById("aiops-monitor").classList.remove("hidden");
    document.getElementById("aiops-report").classList.add("hidden");
    setText("aiops-right-title", "诊断监控");
}

// 入口: 读取/校验输入后, 按"提交方式"分发到 实时 / 排队 两条路径
async function startAiops() {
    const query = document.getElementById("aiops-query").value.trim();
    if (!query) return alert("请输入告警内容");
    return aiopsSubmitMode === "queue"
        ? submitAiopsToQueue(query)
        : runAiopsRealtime(query);
}

// 实时模式: 同步 SSE, 直接流式展示 计划 / 步骤 / token / 报告
async function runAiopsRealtime(query) {
    const planEl = document.getElementById("aiops-plan");
    const stepsEl = document.getElementById("aiops-steps");
    const reportEl = document.getElementById("aiops-report");
    const statusEl = document.getElementById("aiops-status");
    planEl.innerHTML = '<span class="text-slate-400 italic">等待 Planner...</span>';
    stepsEl.innerHTML = "";
    reportEl.innerHTML = "";
    showAiopsMonitor();
    aiopsMonitor.reset();
    statusEl.textContent = "Skill Router 工作中...";
    clearSkillHighlight();
    setAiopsRunning(true);

    aiopsAbortController = new AbortController();
    let hadError = false;
    try {
        const resp = await fetch(`${API}/aiops/diagnose`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                session_id: `web-${Date.now()}`,
                query,
                diagnosis_mode: aiopsDiagnosisMode,
            }),
            signal: aiopsAbortController.signal,
        });
        await consumeSSE(resp, (ev) => {
            if (ev?.type === "error") hadError = true;
            handleAiopsEvent(ev, planEl, stepsEl, reportEl, statusEl);
        });
        if (!hadError) statusEl.textContent = "完成 ✓";
    } catch (e) {
        if (e.name === "AbortError") {
            statusEl.textContent = "已停止";
        } else {
            statusEl.textContent = "失败 ✗";
            showAiopsReport();
            reportEl.innerHTML = `<p style="color:var(--st-failed)">错误: ${escapeHtml(e.message)}</p>`;
        }
    } finally {
        setAiopsRunning(false);
        aiopsAbortController = null;
        aiopsMonitor.stop();
    }
}

// 排队模式: 提交到 Redis 队列, 后台 Worker 执行; 前端轮询任务状态直到出报告。
// 价值: 高并发下 API 立刻返回, 不被长诊断拖住; 能看到"排队位置"。
async function submitAiopsToQueue(query) {
    const planEl = document.getElementById("aiops-plan");
    const stepsEl = document.getElementById("aiops-steps");
    const reportEl = document.getElementById("aiops-report");
    const statusEl = document.getElementById("aiops-status");

    planEl.innerHTML = '<span class="text-slate-400 italic">排队模式 — 任务由后台 Worker 执行</span>';
    stepsEl.innerHTML = '<span class="text-slate-400 italic">提交后在右侧查看任务状态与排队位置</span>';
    clearSkillHighlight();
    showAiopsReport();
    reportEl.innerHTML = '<div class="text-slate-400 italic">提交中...</div>';
    statusEl.textContent = "提交排队中...";
    aiopsStopPolling();
    setAiopsRunning(true);

    try {
        const r = await fetch(`${API}/aiops/diagnose/submit`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ query, mode: aiopsDiagnosisMode, session_id: `web-${Date.now()}` }),
        });
        const data = await r.json().catch(() => null);
        if (r.status === 429) {
            const retry = data?.detail?.retry_after ?? data?.retry_after;
            reportEl.innerHTML = `<p style="color:var(--st-pending)">提交过于频繁，请 ${retry || "稍后"} 秒后重试</p>`;
            statusEl.textContent = "已限流";
            setAiopsRunning(false);
            return;
        }
        if (!r.ok || !data?.task_id) {
            throw new Error(data?.message || data?.detail || `HTTP ${r.status}`);
        }
        statusEl.textContent = data.task_created ? "已入队" : "复用进行中任务";
        aiopsActiveTaskId = data.task_id;
        renderAiopsTaskStatus({
            id: data.task_id, status: "pending",
            queue_position: data.queue_position, payload: {},
        });
        pollAiopsTask(data.task_id);
    } catch (e) {
        reportEl.innerHTML = `<p style="color:var(--st-failed)">提交失败: ${escapeHtml(e.message)}</p>`;
        statusEl.textContent = "失败 ✗";
        setAiopsRunning(false);
    }
}

// 每 2s 轮询一次任务状态, 直到 succeeded/failed/cancelled; 期间被停止/替换则自动退出
function pollAiopsTask(taskId) {
    const tick = async () => {
        if (aiopsActiveTaskId !== taskId) return;
        let task = null;
        try {
            const r = await fetch(`${API}/incidents/tasks/${encodeURIComponent(taskId)}`);
            if (r.ok) task = await r.json();
        } catch (_) { /* 网络抖动, 下一轮再试 */ }
        if (aiopsActiveTaskId !== taskId) return;
        if (task) {
            renderAiopsTaskStatus(task);
            if (["succeeded", "failed", "cancelled"].includes(task.status)) {
                setAiopsRunning(false);
                aiopsActiveTaskId = null;
                return;
            }
        }
        aiopsPollTimer = setTimeout(tick, 2000);
    };
    tick();
}

// 把一条任务的当前状态渲染到报告区 (排队/运行用状态卡, 完成则渲染 markdown 报告)
function renderAiopsTaskStatus(task) {
    const reportEl = document.getElementById("aiops-report");
    const statusEl = document.getElementById("aiops-status");
    const p = task.payload || {};
    const panel = (title, sub) => `
        <div class="border p-4" style="border-color:var(--hairline);background:var(--surface-alt)">
            <div class="flex items-center gap-2">
                <span class="rag-spinner inline-block w-2 h-2" style="background:var(--accent)"></span>
                <span class="font-semibold" style="color:var(--text-primary)">${escapeHtml(title)}</span>
            </div>
            <div class="text-xs mt-1" style="color:var(--text-muted)">${escapeHtml(sub)}</div>
            <div class="text-[10px] font-mono mt-2" style="color:var(--text-muted)">task ${escapeHtml(task.id || "")}</div>
        </div>`;

    switch (task.status) {
        case "pending": {
            const pos = task.queue_position;
            statusEl.textContent = "排队中";
            reportEl.innerHTML = panel("排队中", pos ? `前方还有 ${pos - 1} 个任务` : "等待 Worker 领取");
            break;
        }
        case "running":
            statusEl.textContent = "运行中";
            reportEl.innerHTML = panel("运行中", "后台 Worker 正在诊断…");
            break;
        case "succeeded":
            statusEl.textContent = "报告已生成";
            reportEl.innerHTML = p.report
                ? renderMarkdown(p.report)
                : '<p class="text-slate-400 italic">任务完成，但未返回报告</p>';
            break;
        case "failed":
        case "cancelled":
            statusEl.textContent = task.status === "failed" ? "失败 ✗" : "已取消";
            reportEl.innerHTML = `<p style="color:var(--st-failed)">${task.status === "failed" ? "诊断失败" : "已取消"}: ${escapeHtml(task.error || "")}</p>`;
            break;
    }
}

function handleAiopsEvent(ev, planEl, stepsEl, reportEl, statusEl) {
    const t = ev.type;
    const d = ev.data || {};
    // 诊断: 把所有 SSE 事件类型打到控制台, 方便排查监控为什么是 0
    if (t !== "transition") {
        console.log("[AIOps SSE]", t, d);
    }

    if (t === "start") {
        statusEl.textContent = "Skill Router 工作中...";
    } else if (t === "mode_selected") {
        statusEl.textContent = d.group_agent_reserved
            ? "深度入口已保留, 先走日常诊断"
            : "日常诊断模式";
    } else if (t === "skill_selected") {
        highlightSkill(d.skill, d.reason);
        statusEl.textContent = `已选 Skill: ${d.skill || "(无)"}, Planner 工作中...`;
    } else if (t === "plan") {
        planEl.innerHTML = "";
        (d.plan || []).forEach((step, i) => {
            const div = document.createElement("div");
            div.className = "flex items-start space-x-2";
            div.innerHTML = `<span class="bg-indigo-100 text-indigo-700 rounded-full w-5 h-5 text-xs flex items-center justify-center flex-shrink-0 mt-0.5">${i + 1}</span><span class="text-slate-700">${escapeHtml(step)}</span>`;
            planEl.appendChild(div);
        });
        statusEl.textContent = `已生成 ${d.plan.length} 步计划`;
    } else if (t === "step_start") {
        // 创建 "executing" 卡片, 后续 step_token 往里追加流式内容
        let div = stepsEl.querySelector(`[data-step-iter="${d.iteration}"]`);
        if (!div) {
            div = document.createElement("div");
            div.className = "step-item executing";
            div.dataset.stepIter = String(d.iteration);
            div.innerHTML = `<div class="font-semibold text-xs text-indigo-700 mb-1">▶ 步骤 ${escapeHtml(String(d.iteration))}</div>
                <div class="text-xs text-slate-600 mb-1">${escapeHtml(d.step || "")}</div>
                <div class="step-stream text-xs text-slate-500 whitespace-pre-wrap break-words"></div>`;
            stepsEl.appendChild(div);
        }
        stepsEl.scrollTop = stepsEl.scrollHeight;
        statusEl.textContent = `正在执行第 ${d.iteration} 步...`;
        // 监控面板: 更新当前步骤 + 清空实时输出 (每步重置)
        setText("mon-step", String(d.iteration));
        setText("mon-step-label", (d.step || "").slice(0, 40));
        setText("mon-stream-hint", "生成中...");
        const stream = document.getElementById("mon-stream");
        if (stream) stream.textContent = "";
    } else if (t === "step_token") {
        const iter = d.iteration || 0;
        const content = d.content || "";
        let div = stepsEl.querySelector(`[data-step-iter="${iter}"]`);
        if (!div) {
            // 兜底: 没收到 step_start 就先建一张卡
            div = document.createElement("div");
            div.className = "step-item executing";
            div.dataset.stepIter = String(iter);
            div.innerHTML = `<div class="font-semibold text-xs text-indigo-700 mb-1">▶ 步骤 ${escapeHtml(String(iter))}</div>
                <div class="step-stream text-xs text-slate-500 whitespace-pre-wrap break-words"></div>`;
            stepsEl.appendChild(div);
        }
        const stream = div.querySelector(".step-stream");
        if (stream) {
            stream.textContent += content;
            if (stream.textContent.length > 2000) {
                stream.textContent = "..." + stream.textContent.slice(-1800);
            }
        }
        stepsEl.scrollTop = stepsEl.scrollHeight;
        // 监控面板: 大屏实时输出 + token 累计 (按字符数粗估)
        const monStream = document.getElementById("mon-stream");
        if (monStream) {
            if (monStream.querySelector(".italic")) monStream.textContent = "";
            monStream.textContent += content;
            if (monStream.textContent.length > 4000) {
                monStream.textContent = "..." + monStream.textContent.slice(-3600);
            }
            monStream.scrollTop = monStream.scrollHeight;
        }
        aiopsMonitor.tokenCount += content.length;
        // 真实 usage 还没回来时, 用字符流粗估占位; usage 一到就被覆盖.
        if (!aiopsMonitor.hasRealUsage) {
            setText("mon-tokens", String(aiopsMonitor.tokenCount));
            setText("mon-tokens-detail", `~流字符 ${aiopsMonitor.tokenCount}`);
        }
    } else if (t === "usage") {
        // 后端 tool_runner 在每轮 LLM 末帧 emit, DeepSeek/DashScope 都通过
        // stream_options.include_usage / stream_usage=true 拿到真实 token.
        // 这里把多轮累加, 给 SRE 看真实成本.
        aiopsMonitor.hasRealUsage = true;
        aiopsMonitor.realInputTokens  += d.input_tokens  || 0;
        aiopsMonitor.realOutputTokens += d.output_tokens || 0;
        aiopsMonitor.realTotalTokens  += d.total_tokens  || 0;
        if (d.cache_hit_tokens != null)  aiopsMonitor.cacheHitTokens  += d.cache_hit_tokens;
        if (d.cache_miss_tokens != null) aiopsMonitor.cacheMissTokens += d.cache_miss_tokens;
        setText("mon-tokens", String(aiopsMonitor.realOutputTokens));
        const parts = [
            `输入 ${aiopsMonitor.realInputTokens}`,
            `输出 ${aiopsMonitor.realOutputTokens}`,
        ];
        if (aiopsMonitor.cacheHitTokens > 0 || aiopsMonitor.cacheMissTokens > 0) {
            parts.push(`缓存命中 ${aiopsMonitor.cacheHitTokens}`);
        }
        const detailEl = document.getElementById("mon-tokens-detail");
        if (detailEl) {
            detailEl.textContent = parts.join(" · ");
            detailEl.title = `合计 ${aiopsMonitor.realTotalTokens} tokens` +
                (d.model ? ` · ${d.model}` : "");
        }
        setText("mon-tokens-badge", "API 实测");
    } else if (t === "tool_call") {
        // 监控面板: 工具调用累计 + 流水列表
        aiopsMonitor.toolCount += 1;
        const ok = d.success !== false; // 后端 ok=true / success=true 都算成功
        if (!ok) aiopsMonitor.toolFail += 1;
        setText("mon-tools", String(aiopsMonitor.toolCount));
        setText("mon-tools-fail", `失败 ${aiopsMonitor.toolFail}`);
        const feed = document.getElementById("mon-tool-feed");
        if (feed) {
            // 首次清掉占位
            if (feed.querySelector(".italic")) feed.innerHTML = "";
            const row = document.createElement("div");
            const statusIcon = ok ? "✓" : "✗";
            const statusColor = ok ? "text-emerald-600" : "text-rose-600";
            const elapsed = d.elapsed_ms != null ? `${d.elapsed_ms}ms` : "";
            row.className = "flex items-center gap-2 px-2 py-1 rounded hover:bg-slate-50 border-b border-slate-100";
            row.innerHTML = `<span class="${statusColor} font-semibold">${statusIcon}</span>
                <span class="font-mono text-slate-700 truncate">${escapeHtml(d.name || "?")}</span>
                <span class="text-slate-400 ml-auto shrink-0">${escapeHtml(elapsed)}</span>`;
            feed.appendChild(row);
            feed.scrollTop = feed.scrollHeight;
        }
    } else if (t === "step_complete") {
        // 把之前 executing 的卡片收紧成 done + 替换为结果预览
        const iter = d.iteration || 0;
        let div = stepsEl.querySelector(`[data-step-iter="${iter}"]`);
        if (!div) {
            div = document.createElement("div");
            div.dataset.stepIter = String(iter);
            stepsEl.appendChild(div);
        }
        div.className = "step-item done";
        div.innerHTML = `<div class="font-semibold text-xs text-emerald-700 mb-1">✓ 步骤 ${escapeHtml(String(iter))}</div>
            <div class="text-xs text-slate-600 mb-1">${escapeHtml(d.step || "")}</div>
            <div class="text-xs text-slate-500 italic">${escapeHtml((d.result_preview || "").slice(0, 200))}</div>`;
        stepsEl.scrollTop = stepsEl.scrollHeight;
        statusEl.textContent = `已完成 ${d.iteration} 步`;
    } else if (t === "replan") {
        const div = document.createElement("div");
        div.className = "step-item executing";
        div.innerHTML = `<div class="text-xs" style="color:var(--accent)">Replanner 调整: 剩余 ${(d.plan || []).length} 步</div>`;
        stepsEl.appendChild(div);
        stepsEl.scrollTop = stepsEl.scrollHeight;
    } else if (t === "report") {
        showAiopsReport();
        reportEl.innerHTML = renderMarkdown(d.report || "");
        statusEl.textContent = "报告已生成";
        setText("mon-stream-hint", "已完成");
    } else if (t === "tool_pending_approval") {
        // 工具被 ASK 路由阻塞, 等审批. 在工具流水里加一行黄色待批提示, 并把状态栏标黄
        const feed = document.getElementById("mon-tool-feed");
        if (feed) {
            if (feed.querySelector(".italic")) feed.innerHTML = "";
            const row = document.createElement("div");
            row.className = "flex items-center gap-2 px-2 py-1 border";
            row.style.borderLeft = "2px solid var(--st-pending)";
            row.dataset.approvalId = d.approval_id || "";
            row.innerHTML = `<span class="font-mono truncate" style="color:var(--text-secondary)">${escapeHtml(d.tool || "?")}</span>
                <span class="text-[10px] ml-auto shrink-0" style="color:var(--st-pending)">待审批</span>`;
            feed.appendChild(row);
            feed.scrollTop = feed.scrollHeight;
        }
        statusEl.textContent = `工具 ${d.tool || "?"} 待人工审批 (id=${d.approval_id || "?"}), 去顶栏"审批"处理`;
        // 抢一次审批列表刷新 (renderApprovalBell 会据数量给铃加红色强调)
        if (typeof loadApprovals === "function") loadApprovals();
    } else if (t === "tool_approval_resolved") {
        const feed = document.getElementById("mon-tool-feed");
        if (feed && d.approval_id) {
            const row = feed.querySelector(`[data-approval-id="${CSS.escape(d.approval_id)}"]`);
            if (row) {
                const ok = d.status === "approved";
                row.className = "flex items-center gap-2 px-2 py-1 border";
                row.style.borderLeft = `2px solid ${ok ? "var(--st-success)" : "var(--st-failed)"}`;
                const col = ok ? "var(--st-success)" : "var(--st-failed)";
                const icon = ok ? "✓" : "✗";
                row.innerHTML = `<span class="font-semibold" style="color:${col}">${icon}</span>
                    <span class="font-mono truncate" style="color:${col}">${escapeHtml(d.tool || "?")}</span>
                    <span class="text-[10px] ml-auto shrink-0" style="color:${col}">${escapeHtml(d.status || "?")}</span>`;
            }
        }
        if (typeof loadApprovals === "function") loadApprovals();
    } else if (t === "complete") {
        statusEl.textContent = "完成 ✓";
    } else if (t === "error") {
        showAiopsReport();
        // 并发已满: 不是死路, 给一个"改为排队提交"的一键出口 (端到端打通排队体验)
        const limited = ev.stage === "concurrency_limited" || /并发|稍后重试|排队/.test(ev.message || "");
        const friendly = friendlyAiopsError(ev);
        reportEl.innerHTML =
            `<p style="color:var(--st-failed)">${escapeHtml(friendly.title)}</p>` +
            (friendly.detail ? `<p class="text-xs mt-2 whitespace-pre-wrap" style="color:var(--text-muted)">${escapeHtml(friendly.detail)}</p>` : "") +
            (limited ? `<button id="aiops-fallback-queue" class="mt-2 px-3 py-1.5 text-xs text-white" style="background:var(--accent)">改为排队提交</button>` : "");
        statusEl.textContent = "失败 ✗";
        if (limited) {
            const btn = document.getElementById("aiops-fallback-queue");
            if (btn) btn.addEventListener("click", () => {
                const q = document.getElementById("aiops-query").value.trim();
                if (q) submitAiopsToQueue(q);
            });
        }
    }
}

function friendlyAiopsError(ev) {
    const msg = ev?.message || "";
    const data = ev?.data || {};
    const raw = [msg, data.error_type, data.error, data.detail].filter(Boolean).join("\n");
    if (/402|Insufficient Balance|余额不足|quota|额度不足/i.test(raw)) {
        return {
            title: "模型调用失败：账号余额或额度不足",
            detail: "请检查 .env 中配置的模型 API Key 对应账号是否还有余额，或切换到可用的模型/Key 后重新启动服务。",
        };
    }
    if (/401|unauthorized|invalid api key|api key/i.test(raw)) {
        return {
            title: "模型调用失败：API Key 无效或未授权",
            detail: "请检查 .env 中的 DASHSCOPE_API_KEY / DEEPSEEK_API_KEY 等模型配置。",
        };
    }
    return { title: `错误: ${msg}`, detail: "" };
}

// ============================================================
// RAG Chat
// ============================================================
const chatInput = document.getElementById("chat-input");
const chatSend = document.getElementById("chat-send");
const chatWebToggle = document.getElementById("chat-web-toggle");
const chatWebState = document.getElementById("chat-web-state");
const chatMcpToggle = document.getElementById("chat-mcp-toggle");
const chatMcpState = document.getElementById("chat-mcp-state");
let chatWebEnabled = false;
let chatMcpEnabled = true;

function renderChatWebToggle() {
    if (!chatWebToggle) return;
    chatWebToggle.className = "px-3 py-2 border text-xs font-medium select-none transition hover:bg-slate-100";
    if (chatWebEnabled) {
        chatWebToggle.style.borderColor = "var(--accent)";
        chatWebToggle.style.color = "var(--accent)";
        chatWebState.textContent = "开";
    } else {
        chatWebToggle.style.borderColor = "var(--hairline)";
        chatWebToggle.style.color = "var(--text-muted)";
        chatWebState.textContent = "关";
    }
}
if (chatWebToggle) {
    chatWebToggle.addEventListener("click", () => {
        chatWebEnabled = !chatWebEnabled;
        renderChatWebToggle();
    });
    renderChatWebToggle();
}

function renderChatMcpToggle() {
    if (!chatMcpToggle) return;
    chatMcpToggle.className = "px-3 py-2 border text-xs font-medium select-none transition hover:bg-slate-100";
    if (chatMcpEnabled) {
        chatMcpToggle.style.borderColor = "var(--accent)";
        chatMcpToggle.style.color = "var(--accent)";
        chatMcpState.textContent = "开";
    } else {
        chatMcpToggle.style.borderColor = "var(--hairline)";
        chatMcpToggle.style.color = "var(--text-muted)";
        chatMcpState.textContent = "关";
    }
}
if (chatMcpToggle) {
    chatMcpToggle.addEventListener("click", () => {
        chatMcpEnabled = !chatMcpEnabled;
        renderChatMcpToggle();
    });
    renderChatMcpToggle();
}

chatSend.addEventListener("click", sendChat);
chatInput.addEventListener("keydown", (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
        e.preventDefault();
        sendChat();
    }
});

async function sendChat() {
    const question = chatInput.value.trim();
    if (!question) return;
    chatInput.value = "";

    appendChatMsg("user", question);
    const progressBox = appendChatProgress();
    const thinkingBubble = appendThinkingBubble();
    thinkingBubble.wrap.style.display = "none"; // 等有 reasoning 再显
    const assistantBubble = appendChatMsg("assistant", "");
    assistantBubble.parentElement.style.display = "none"; // 等第一个 token 再显
    chatSend.disabled = true;

    try {
        const resp = await fetch(`${API}/chat/stream`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                session_id: "web-chat",
                question,
                web_search: chatWebEnabled,
                mcp_tools: chatMcpEnabled,
            }),
        });

        let buf = "";
        let thinkBuf = "";
        let tokenStarted = false;
        let thinkingStarted = false;
        await consumeSSE(resp, (ev) => {
            if (ev.type === "progress") {
                appendChatProgressRow(progressBox, ev);
            } else if (ev.type === "thinking") {
                if (!thinkingStarted) {
                    thinkingStarted = true;
                    thinkingBubble.wrap.style.display = "";
                }
                thinkBuf += ev.content;
                thinkingBubble.content.textContent = thinkBuf;
                const container = document.getElementById("chat-messages");
                container.scrollTop = container.scrollHeight;
            } else if (ev.type === "token") {
                if (!tokenStarted) {
                    tokenStarted = true;
                    finalizeChatProgress(progressBox);
                    // 答案开始时把思考气泡自动折叠 (仍可点开)
                    if (thinkingStarted) collapseThinkingBubble(thinkingBubble);
                    assistantBubble.parentElement.style.display = "";
                }
                buf += ev.content;
                assistantBubble.innerHTML = renderMarkdown(buf);
                const container = document.getElementById("chat-messages");
                container.scrollTop = container.scrollHeight;
            } else if (ev.type === "error") {
                finalizeChatProgress(progressBox, true);
                assistantBubble.parentElement.style.display = "";
                assistantBubble.innerHTML = `<span class="text-red-500">错误: ${escapeHtml(ev.message)}</span>`;
            }
        });
        if (!tokenStarted) {
            // 没拿到任何 token, 清理占位气泡
            assistantBubble.parentElement.remove();
        }
        if (!thinkingStarted) {
            thinkingBubble.wrap.remove();
        }
    } catch (e) {
        finalizeChatProgress(progressBox, true);
        assistantBubble.parentElement.style.display = "";
        assistantBubble.innerHTML = `<span class="text-red-500">网络错误: ${e.message}</span>`;
    } finally {
        chatSend.disabled = false;
        chatInput.focus();
    }
}

// --- RAG Chat 思考过程气泡 (qwen3/qwen-plus-latest 等支持 thinking 的模型才会有) ---
function appendThinkingBubble() {
    const container = document.getElementById("chat-messages");
    const placeholder = container.querySelector(".text-center.italic");
    if (placeholder) placeholder.remove();

    const wrap = document.createElement("div");
    wrap.className = "flex justify-start";
    wrap.innerHTML = `
      <div class="rag-thinking bg-slate-50 border border-slate-200 rounded-lg px-3 py-2 text-xs text-slate-500 max-w-[85%] space-y-1">
        <div class="rag-thinking-head flex items-center gap-1.5 cursor-pointer select-none">
          <span class="font-medium text-slate-600">思考过程</span>
          <span class="rag-thinking-toggle ml-auto text-[10px] text-slate-400">▼ 收起</span>
        </div>
        <pre class="rag-thinking-content whitespace-pre-wrap font-sans text-[11px] leading-relaxed text-slate-500 max-h-48 overflow-auto"></pre>
      </div>`;
    container.appendChild(wrap);
    container.scrollTop = container.scrollHeight;

    const box = wrap.querySelector(".rag-thinking");
    const content = wrap.querySelector(".rag-thinking-content");
    const head = wrap.querySelector(".rag-thinking-head");
    const toggle = wrap.querySelector(".rag-thinking-toggle");
    head.addEventListener("click", () => {
        const hidden = content.classList.toggle("hidden");
        toggle.textContent = hidden ? "▶ 展开" : "▼ 收起";
    });
    return { wrap, box, content, head, toggle };
}

function collapseThinkingBubble(bundle) {
    if (!bundle || !bundle.content) return;
    bundle.content.classList.add("hidden");
    if (bundle.toggle) bundle.toggle.textContent = "▶ 展开";
}

// --- RAG Chat 进度条 (类似 AIOps 步骤卡片) ---
function appendChatProgress() {
    const container = document.getElementById("chat-messages");
    const placeholder = container.querySelector(".text-center.italic");
    if (placeholder) placeholder.remove();

    const wrap = document.createElement("div");
    wrap.className = "flex justify-start";
    wrap.innerHTML = `
      <div class="rag-progress border px-3 py-2 text-xs text-slate-600 space-y-1 max-w-[85%]" style="background: var(--surface-alt);">
        <div class="rag-progress-head font-medium flex items-center gap-2" style="color: var(--accent);">
          <span class="rag-spinner status-dot is-running inline-block"></span>
          <span>正在检索并生成回答…</span>
        </div>
        <div class="rag-progress-rows space-y-0.5"></div>
      </div>`;
    container.appendChild(wrap);
    container.scrollTop = container.scrollHeight;
    return wrap.querySelector(".rag-progress");
}

function appendChatProgressRow(box, ev) {
    if (!box) return;
    const rows = box.querySelector(".rag-progress-rows");
    const icon = iconForRagStage(ev.stage);
    const elapsed = Number.isFinite(ev.elapsed_ms) && ev.elapsed_ms > 0
        ? `<span class="ml-1 text-[10px] text-indigo-500">${ev.elapsed_ms}ms</span>`
        : "";

    const detailsHtml = renderRagStageDetails(ev.stage, ev.data || {});
    const hasDetails = !!detailsHtml;

    const row = document.createElement("div");
    row.className = "rag-progress-row";

    const headLine = document.createElement("div");
    headLine.className = "flex items-center gap-1.5 flex-wrap" + (hasDetails ? " cursor-pointer hover:bg-indigo-100/40 rounded px-0.5 -mx-0.5" : "");
    headLine.innerHTML = `
      <span class="shrink-0">${icon}</span>
      <span class="text-slate-700 font-medium">${escapeHtml(ev.label || ev.stage || "")}</span>
      ${ev.detail ? `<span class="text-slate-400 truncate">${escapeHtml(ev.detail)}</span>` : ""}
      ${elapsed}
      ${hasDetails ? `<span class="rag-toggle text-[10px] text-indigo-500 ml-auto select-none">▶ 详情</span>` : ""}`;
    row.appendChild(headLine);

    if (hasDetails) {
        const panel = document.createElement("div");
        panel.className = "rag-details mt-1 ml-5 hidden text-[11px] text-slate-600 bg-white border border-indigo-100 rounded p-2 space-y-1";
        panel.innerHTML = detailsHtml;
        row.appendChild(panel);
        headLine.addEventListener("click", () => {
            const opened = !panel.classList.contains("hidden");
            panel.classList.toggle("hidden");
            const tog = headLine.querySelector(".rag-toggle");
            if (tog) tog.textContent = opened ? "▶ 详情" : "▼ 收起";
        });
    }

    rows.appendChild(row);
    const container = document.getElementById("chat-messages");
    container.scrollTop = container.scrollHeight;
}

function renderRagStageDetails(stage, data) {
    if (!data || typeof data !== "object") return "";
    if (stage === "rewrite_done") {
        const orig = data.original || "";
        const rew = data.rewritten || "";
        if (!orig && !rew) return "";
        return `
          <div><span class="text-slate-400">原始:</span> ${escapeHtml(orig)}</div>
          <div><span class="text-slate-400">改写:</span> ${escapeHtml(rew)}</div>`;
    }
    if (stage === "retrieve_done") {
        const hits = Array.isArray(data.hits) ? data.hits : [];
        if (!hits.length) return `<div class="text-slate-400">无命中片段</div>`;
        const meta = `<div class="text-slate-400 mb-1">top_k=${data.top_k ?? "?"} · candidate_k=${data.candidate_k ?? "?"} · ${escapeHtml(data.mode || data.pipeline || "")}</div>`;
        const items = hits.map((h, i) => {
            const score = (h.score !== null && h.score !== undefined) ? `<span class="text-emerald-600">score ${h.score}</span>` : "";
            const chap = h.chapter ? ` · 章节: ${escapeHtml(h.chapter)}` : "";
            return `
              <div class="border-l-2 border-indigo-200 pl-2">
                <div class="font-medium text-slate-700">${i + 1}. ${escapeHtml(h.source || "未知")} ${score}${chap}</div>
                <div class="text-slate-500">${escapeHtml(h.preview || "")}</div>
              </div>`;
        }).join("");
        return meta + items;
    }
    if (stage === "web_done") {
        const results = Array.isArray(data.results) ? data.results : [];
        if (!results.length) {
            const reason = data.skip_reason || "未触发联网";
            return `<div class="text-slate-400">${escapeHtml(reason)}</div>`;
        }
        const meta = data.provider ? `<div class="text-slate-400 mb-1">provider=${escapeHtml(data.provider)}</div>` : "";
        const items = results.map((r, i) => {
            const url = r.url || "";
            const titleEsc = escapeHtml(r.title || "(无标题)");
            const titleHtml = url
                ? `<a href="${escapeHtml(url)}" target="_blank" rel="noopener" class="text-indigo-600 hover:underline">${titleEsc}</a>`
                : titleEsc;
            return `
              <div class="border-l-2 border-emerald-200 pl-2">
                <div class="font-medium">${i + 1}. ${titleHtml}</div>
                ${url ? `<div class="text-[10px] text-slate-400 break-all">${escapeHtml(url)}</div>` : ""}
                <div class="text-slate-500">${escapeHtml(r.snippet || "")}</div>
              </div>`;
        }).join("");
        return meta + items;
    }
    if (stage === "stats") {
        return `
          <div>模型: <span class="font-medium">${escapeHtml(data.model || "?")}</span></div>
          <div>输入 tokens: <span class="font-medium">${data.input_tokens ?? 0}</span></div>
          <div>输出 tokens: <span class="font-medium">${data.output_tokens ?? 0}</span></div>
          <div>合计 tokens: <span class="font-medium">${data.total_tokens ?? 0}</span></div>
          <div>生成耗时: <span class="font-medium">${data.llm_ms ?? 0} ms</span></div>
          <div>总耗时: <span class="font-medium">${data.total_ms ?? 0} ms</span></div>
          <div>回答字数: <span class="font-medium">${data.answer_chars ?? 0}</span></div>
          ${data.tools_enabled ? '<div class="text-emerald-600">工具回合: 已启用</div>' : ''}`;
    }
    if (stage === "llm_start") {
        const tools = Array.isArray(data.tools) ? data.tools : [];
        if (data.tools_enabled && tools.length) {
            const chips = tools.map(name => `<span class="inline-block px-1.5 py-0.5 mr-1 mb-1 font-mono text-[10px] border" style="background: var(--surface-alt); color: var(--text-secondary); border-color: var(--hairline);">${escapeHtml(name)}</span>`).join("");
            return `
              <div class="text-slate-500 mb-1">模型: <span class="font-medium">${escapeHtml(data.model || "?")}</span></div>
              <div class="text-slate-500 mb-1">已为模型启用 ${tools.length} 个只读工具, 模型可按需自主调用:</div>
              <div class="flex flex-wrap">${chips}</div>`;
        }
        return `<div class="text-slate-500">模型: <span class="font-medium">${escapeHtml(data.model || "?")}</span> · 工具回合: 未启用</div>`;
    }
    if (stage === "tool_call") {
        const ok = (data.status || "").toLowerCase() === "ok";
        const statusColor = ok ? "text-emerald-600" : "text-rose-600";
        const statusIcon = ok ? "✓" : "✗";
        return `
          <div>工具: <span class="font-mono text-slate-700">${escapeHtml(data.name || "?")}</span></div>
          <div>状态: <span class="${statusColor} font-medium">${statusIcon} ${escapeHtml(data.status || "?")}</span></div>
          <div>耗时: <span class="font-medium">${data.elapsed_ms ?? 0} ms</span></div>
          <div>输出: <span class="font-medium">${data.result_chars ?? 0} 字符</span></div>
          ${data.read_only === false ? '<div class="text-amber-600">⚠ 非只读工具</div>' : ''}`;
    }
    return "";
}

function finalizeChatProgress(box, failed = false) {
    if (!box) return;
    const head = box.querySelector(".rag-progress-head");
    if (head) {
        head.innerHTML = failed
            ? `<span class="text-red-500">✗ 检索流程中断</span>`
            : `<span class="text-emerald-600">✓ 检索流程完成</span>`;
    }
}

function iconForRagStage(stage) {
    // 极简: 进度行已有文字标签, 这里只用单色 done/进行中 标记, 不用 emoji.
    switch (stage) {
        case "rewrite_done":
        case "retrieve_done":
        case "web_done":
        case "stats":        return "·";
        default:             return "·";
    }
}

function appendChatMsg(role, content) {
    const container = document.getElementById("chat-messages");
    // 清掉初始提示
    const placeholder = container.querySelector(".text-center.italic");
    if (placeholder) placeholder.remove();

    const wrap = document.createElement("div");
    wrap.className = "flex " + (role === "user" ? "justify-end" : "justify-start");
    const bubble = document.createElement("div");
    bubble.className = `chat-msg ${role}`;
    bubble.innerHTML = role === "user" ? escapeHtml(content) : renderMarkdown(content);
    wrap.appendChild(bubble);
    container.appendChild(wrap);
    container.scrollTop = container.scrollHeight;
    return bubble;
}

// ============================================================
// Incident 工作台
// ============================================================
// 设计思路:
//   - 列表 + 详情两栏, 共享 incidents.items 缓存
//   - 自动 5s 拉新; 当前选中任务还在 pending/running 时, 同步刷新详情
//   - 详情面板组装: 概览 KV → 触发输入 → 错误 → 报告 markdown → 证据链 (按 source 分组) → Agent Runs → Tool Calls
//   - 后端 API: 见 app/api/v1/incidents.py (tasks / tasks/{id} / .../evidence / .../agent-runs / .../tool-calls)
//   - 后端不可用时 (Postgres 未就绪等) 优雅降级, 不打断其他 Tab.

const incidents = {
    items: [],
    selectedId: null,
    selectedIds: new Set(),
    filterStatus: "all",
    search: "",
    auto: true,
    timer: null,
    inflightList: false,
    inflightDetail: false,
    bulkDeleting: false,
};

function incOnTabEnter() {
    loadIncidents();
    loadQueueStatus();
    incScheduleAutoRefresh();
}

function incOnTabLeave() {
    if (incidents.timer) {
        clearInterval(incidents.timer);
        incidents.timer = null;
    }
}

async function loadQueueStatus() {
    const card = document.getElementById("inc-queue-card");
    if (!card) return;
    try {
        const r = await fetch(`${API}/queue/status`);
        if (!r.ok) throw new Error(`HTTP ${r.status}`);
        const data = await r.json();
        if (!data.configured) {
            card.classList.add("hidden");
            return;
        }
        card.classList.remove("hidden");
        setText("inc-q-depth", data.depth != null ? String(data.depth) : "—");
        setText("inc-q-pending", data.pending != null ? String(data.pending) : "—");
        setText("inc-q-workers", data.alive_workers != null ? `${data.alive_workers}/${(data.workers || []).length}` : `${(data.workers || []).length}`);
        setText("inc-q-dlq", data.dlq_depth != null ? String(data.dlq_depth) : "—");
        // 并发槽占用 (分布式限流): 手动 / Worker
        const slots = data.slots || {};
        const fmtSlot = (s) => (s && s.used != null) ? `${s.used}/${s.limit}` : "—";
        setText("inc-q-slot-manual", fmtSlot(slots.manual_diagnosis));
        setText("inc-q-slot-worker", fmtSlot(slots.worker_diagnosis));
        // 优先级队列各级深度 (步骤4): critical/high/normal/low
        let levelStr = "";
        if (data.priority_enabled && data.depth_by_level) {
            const lv = data.depth_by_level;
            const order = ["critical", "high", "normal", "low"];
            levelStr = " · " + order.filter((k) => lv[k] != null).map((k) => `${k[0].toUpperCase()}:${lv[k]}`).join(" ");
        }
        setText("inc-q-stream", `group=${data.consumer_group || "?"}${levelStr}`);
        const warnEl = document.getElementById("inc-q-warnings");
        if (warnEl) {
            const warns = data.warnings || [];
            warnEl.textContent = warns.length ? `⚠ ${warns.join(" · ")}` : "";
        }
    } catch (e) {
        // 静默隐藏卡片, 不打断事件中心列表
        card.classList.add("hidden");
    }
}

function incScheduleAutoRefresh() {
    if (incidents.timer) {
        clearInterval(incidents.timer);
        incidents.timer = null;
    }
    if (!incidents.auto) return;
    incidents.timer = setInterval(() => {
        loadIncidents(true);
        loadQueueStatus();
        // 选中的任务还在跑就同步刷新详情
        if (incidents.selectedId) {
            const cur = incidents.items.find((t) => t.id === incidents.selectedId);
            if (cur && (cur.status === "pending" || cur.status === "running")) {
                loadIncidentDetail(incidents.selectedId, true);
            }
        }
    }, 5000);
}

async function loadIncidents(silent = false) {
    if (incidents.inflightList) return;
    incidents.inflightList = true;
    try {
        const r = await fetch(`${API}/incidents/tasks?limit=20`);
        if (!r.ok) throw new Error(`HTTP ${r.status}`);
        const data = await r.json();
        incidents.items = Array.isArray(data?.items) ? data.items : [];
        const deletableIds = new Set(
            incidents.items.filter(isIncidentDeletable).map((item) => item.id),
        );
        incidents.selectedIds = new Set(
            [...incidents.selectedIds].filter((taskId) => deletableIds.has(taskId)),
        );
        renderIncidentStats();
        renderIncidentList();
    } catch (e) {
        if (!silent) {
            const listEl = document.getElementById("inc-list");
            if (listEl) {
                listEl.innerHTML = `
                    <div class="text-rose-500 text-center py-8 text-xs">
                        加载失败: ${escapeHtml(e.message)}
                        <div class="text-slate-400 text-[11px] mt-1">请确认后端服务与 Postgres 已启动</div>
                    </div>`;
            }
            ["inc-stat-total", "inc-stat-running", "inc-stat-pending", "inc-stat-succeeded", "inc-stat-failed"]
                .forEach((id) => setText(id, "—"));
        }
    } finally {
        incidents.inflightList = false;
    }
}

function renderIncidentStats() {
    const items = incidents.items || [];
    const by = { pending: 0, running: 0, succeeded: 0, failed: 0 };
    items.forEach((t) => {
        if (by[t.status] !== undefined) by[t.status] += 1;
    });
    setText("inc-stat-total", String(items.length));
    setText("inc-stat-running", String(by.running));
    setText("inc-stat-pending", String(by.pending));
    setText("inc-stat-succeeded", String(by.succeeded));
    setText("inc-stat-failed", String(by.failed));
    // 失败计数 >0 时数字变红 (唯一允许的状态着色), 否则保持中性 graphite
    const failedEl = document.getElementById("inc-stat-failed");
    if (failedEl) failedEl.classList.toggle("is-failed", by.failed > 0);
}

function isIncidentDeletable(task) {
    return !!task?.id && task.status !== "pending" && task.status !== "running";
}

function getFilteredIncidentItems() {
    const q = (incidents.search || "").toLowerCase().trim();
    const status = incidents.filterStatus;
    return (incidents.items || []).filter((t) => {
        if (status !== "all" && t.status !== status) return false;
        if (!q) return true;
        const p = t.payload || {};
        const hay = `${t.id || ""} ${p.alertname || ""} ${p.service || ""} ${p.query || ""} ${p.instance || ""}`.toLowerCase();
        return hay.includes(q);
    });
}

function syncIncidentBulkControls(filtered = getFilteredIncidentItems()) {
    const selectedCount = incidents.selectedIds.size;
    const countEl = document.getElementById("inc-selected-count");
    const deleteBtn = document.getElementById("inc-bulk-delete");
    const selectAll = document.getElementById("inc-select-all");
    const visibleDeletable = filtered.filter(isIncidentDeletable);
    const visibleSelected = visibleDeletable.filter((task) => incidents.selectedIds.has(task.id)).length;

    if (countEl) countEl.textContent = `已选 ${selectedCount}`;
    if (deleteBtn) {
        deleteBtn.disabled = selectedCount === 0 || incidents.bulkDeleting;
        deleteBtn.textContent = incidents.bulkDeleting ? "删除中..." : selectedCount ? `删除 ${selectedCount} 条` : "删除";
    }
    if (selectAll) {
        selectAll.disabled = visibleDeletable.length === 0 || incidents.bulkDeleting;
        selectAll.checked = visibleDeletable.length > 0 && visibleSelected === visibleDeletable.length;
        selectAll.indeterminate = visibleSelected > 0 && visibleSelected < visibleDeletable.length;
    }
}

function renderIncidentList() {
    const el = document.getElementById("inc-list");
    if (!el) return;
    const filtered = getFilteredIncidentItems();

    if (filtered.length === 0) {
        el.innerHTML = `<div class="text-slate-400 italic text-center py-8">${incidents.items.length === 0 ? "暂无诊断任务, 先去 AIOps Tab 跑一次" : "当前过滤条件下无匹配任务"}</div>`;
        syncIncidentBulkControls(filtered);
        return;
    }

    el.innerHTML = "";
    filtered.forEach((t) => {
        const p = t.payload || {};
        const card = document.createElement("div");
        const checked = incidents.selectedIds.has(t.id);
        const deletable = isIncidentDeletable(t);
        card.className = `inc-task ${incidents.selectedId === t.id ? "selected" : ""} ${checked ? "bulk-selected" : ""}`;
        card.dataset.taskId = t.id;
        const title = p.alertname || p.query || "(无标题)";
        const idTail = (t.id || "").slice(-8);
        const svc = p.service ? `<div class="text-[11px] text-slate-500 font-mono truncate">${escapeHtml(p.service)}${p.instance ? " · " + escapeHtml(p.instance) : ""}</div>` : "";
        const retries = (t.attempts || 0) > 1 ? `<span class="text-amber-600">· 重试 ${t.attempts}</span>` : "";
        card.innerHTML = `
            <div class="flex items-center gap-2 mb-1.5">
                <input type="checkbox"
                    class="inc-task-check"
                    data-inc-select="${escapeHtml(t.id || "")}"
                    ${checked ? "checked" : ""}
                    ${deletable ? "" : "disabled title=\"任务结束后才能删除\""}
                    aria-label="选择 ${escapeHtml(title)}" />
                ${renderStatusBadge(t.status)}
                <span class="text-[10px] text-slate-400 font-mono ml-auto" title="${escapeHtml(t.id || "")}">…${escapeHtml(idTail)}</span>
            </div>
            <div class="font-semibold text-slate-700 truncate mb-0.5">
                ${renderSevDot(p.severity)}${escapeHtml(title)}
            </div>
            ${svc}
            <div class="flex items-center gap-2 mt-1.5 text-[10px] text-slate-400">
                <span title="${escapeHtml(t.created_at || "")}">${timeAgo(t.created_at)}</span>
                <span>·</span>
                <span class="font-mono">${escapeHtml(t.diagnosis_mode || "fast")}</span>
                ${retries}
            </div>`;
        card.addEventListener("click", () => selectIncidentTask(t.id));
        const checkbox = card.querySelector("[data-inc-select]");
        if (checkbox) {
            checkbox.addEventListener("click", (event) => event.stopPropagation());
            checkbox.addEventListener("change", (event) => {
                event.stopPropagation();
                if (event.target.checked) incidents.selectedIds.add(t.id);
                else incidents.selectedIds.delete(t.id);
                card.classList.toggle("bulk-selected", event.target.checked);
                syncIncidentBulkControls(filtered);
            });
        }
        el.appendChild(card);
    });
    syncIncidentBulkControls(filtered);
}

async function selectIncidentTask(taskId) {
    incidents.selectedId = taskId;
    document.querySelectorAll(".inc-task").forEach((c) => {
        c.classList.toggle("selected", c.dataset.taskId === taskId);
    });
    const detail = document.getElementById("inc-detail");
    if (detail) {
        detail.innerHTML = `<div class="text-center text-slate-400 italic py-8">加载详情...</div>`;
    }
    await loadIncidentDetail(taskId);
}

async function loadIncidentDetail(taskId, silent = false) {
    if (!taskId) return;
    if (incidents.inflightDetail && silent) return;
    incidents.inflightDetail = true;
    try {
        const enc = encodeURIComponent(taskId);
        const [taskR, evR, arR, tcR] = await Promise.all([
            fetch(`${API}/incidents/tasks/${enc}`),
            fetch(`${API}/incidents/tasks/${enc}/evidence?limit=100`).catch(() => null),
            fetch(`${API}/incidents/tasks/${enc}/agent-runs`).catch(() => null),
            fetch(`${API}/incidents/tasks/${enc}/tool-calls`).catch(() => null),
        ]);
        if (!taskR.ok) throw new Error(`HTTP ${taskR.status}`);
        const task = await taskR.json();
        const evidence = evR && evR.ok ? (await evR.json())?.items || [] : [];
        const agentRuns = arR && arR.ok ? (await arR.json())?.items || [] : [];
        const toolCalls = tcR && tcR.ok ? (await tcR.json())?.items || [] : [];
        // 用户可能在请求飞行期间切换了选中, 只渲染仍被选中的任务
        if (incidents.selectedId === taskId) {
            renderIncidentDetail(task, evidence, agentRuns, toolCalls);
        }
    } catch (e) {
        if (!silent && incidents.selectedId === taskId) {
            const detail = document.getElementById("inc-detail");
            if (detail) {
                detail.innerHTML = `<div class="text-rose-500 py-8 text-center">详情加载失败: ${escapeHtml(e.message)}</div>`;
            }
        }
    } finally {
        incidents.inflightDetail = false;
    }
}

function renderIncidentDetail(task, evidence, agentRuns, toolCalls) {
    const detail = document.getElementById("inc-detail");
    if (!detail) return;
    const p = task.payload || {};
    const report = p.report || "";
    const error = task.error || "";
    const title = p.alertname || p.query || "(无标题)";

    const parts = [];

    // 头部
    parts.push(`
        <div class="mb-3">
            <div class="flex items-center gap-2 mb-1 flex-wrap">
                ${renderStatusBadge(task.status)}
                <span class="text-xs text-slate-500">模式 <span class="font-mono text-slate-700">${escapeHtml(task.diagnosis_mode || "fast")}</span></span>
                ${task.attempts ? `<span class="text-xs text-slate-500">尝试 ${task.attempts}/${task.max_attempts || "?"}</span>` : ""}
                ${task.priority != null ? `<span class="text-xs text-slate-500">优先级 ${task.priority}</span>` : ""}
                <button
                    data-inc-delete="${escapeHtml(task.id || "")}"
                    class="ml-auto border border-rose-300 px-2 py-1 text-xs text-rose-600 hover:bg-rose-50 disabled:cursor-not-allowed disabled:opacity-40"
                    ${task.status === "pending" || task.status === "running" ? "disabled title=\"任务结束后才能删除\"" : ""}
                >删除</button>
            </div>
            <h2 class="text-lg font-bold text-slate-800 break-words">
                ${renderSevDot(p.severity)}${escapeHtml(title)}
            </h2>
            <div class="text-[11px] text-slate-400 font-mono mt-1 flex items-center gap-2">
                <span title="${escapeHtml(task.id || "")}">ID: ${escapeHtml(task.id || "")}</span>
                <button data-inc-copy="${escapeHtml(task.id || "")}" class="text-indigo-500 hover:underline">复制</button>
            </div>
        </div>`);

    // 概览
    const kvRows = [];
    kvRows.push(`<dt>告警名</dt><dd>${escapeHtml(p.alertname || "(无)")}</dd>`);
    if (p.service)     kvRows.push(`<dt>服务</dt><dd>${escapeHtml(p.service)}</dd>`);
    if (p.instance)    kvRows.push(`<dt>实例</dt><dd>${escapeHtml(p.instance)}</dd>`);
    if (p.severity)    kvRows.push(`<dt>严重等级</dt><dd>${escapeHtml(p.severity)}</dd>`);
    if (p.fingerprint) kvRows.push(`<dt>指纹</dt><dd>${escapeHtml(p.fingerprint)}</dd>`);
    kvRows.push(`<dt>创建时间</dt><dd>${escapeHtml(task.created_at || "—")}</dd>`);
    if (task.claimed_at)  kvRows.push(`<dt>领取时间</dt><dd>${escapeHtml(task.claimed_at)}</dd>`);
    if (task.finished_at) kvRows.push(`<dt>完成时间</dt><dd>${escapeHtml(task.finished_at)} · 耗时 ${formatDuration(task.claimed_at || task.created_at, task.finished_at)}</dd>`);
    if (task.incident_group_id) kvRows.push(`<dt>事件组</dt><dd>${escapeHtml(task.incident_group_id)}</dd>`);
    if (task.status === "pending" && task.queue_position) {
        kvRows.push(`<dt>排队位置</dt><dd style="color:var(--st-pending)">第 ${task.queue_position} 位 · 前方还有 ${task.queue_position - 1} 个</dd>`);
    }
    if (task.repeat_count) kvRows.push(`<dt>重复命中</dt><dd>${task.repeat_count} 次 (去重合并)</dd>`);
    parts.push(`<div class="inc-section-title">概览</div><dl class="inc-kv">${kvRows.join("")}</dl>`);

    // 触发输入
    if (p.query) {
        parts.push(`<div class="inc-section-title">触发输入</div>
            <div class="bg-slate-50 border p-3 text-xs text-slate-700 whitespace-pre-wrap break-words">${escapeHtml(p.query)}</div>`);
    }

    // 错误
    if (error) {
        parts.push(`<div class="inc-section-title" style="color:var(--st-failed)">错误</div>
            <pre class="border p-3 text-xs whitespace-pre-wrap break-all" style="background:var(--surface-alt); color:var(--st-failed); border-color:var(--hairline);">${escapeHtml(error)}</pre>`);
    }

    // 报告
    if (report) {
        parts.push(`<div class="inc-section-title">诊断报告</div>
            <div class="prose prose-sm max-w-none border p-4 bg-white">${renderMarkdown(report)}</div>`);
    } else if (task.status === "pending" || task.status === "running") {
        parts.push(`<div class="inc-section-title">诊断报告</div>
            <div class="text-slate-400 italic text-center py-4 border bg-slate-50">诊断进行中, 报告生成后会自动刷新...</div>`);
    }

    // 关键信号: 把 RCA + top-N 高分证据顶在前面, 让"根因候选 → 支撑证据"一目了然
    if (evidence.length > 0) {
        const rcaEvs = evidence.filter((e) => e.source === "rca");
        const scoredEvs = evidence
            .filter((e) => typeof e.score === "number" && !isNaN(e.score) && e.source !== "rca")
            .sort((a, b) => (b.score || 0) - (a.score || 0))
            .slice(0, 3);
        const keyItems = [...rcaEvs, ...scoredEvs];
        if (keyItems.length > 0) {
            parts.push(`<div class="inc-section-title">关键信号</div>`);
            const items = keyItems.map((ev) => {
                const src = ev.source || "unknown";
                const safeSrc = String(src).replace(/[^a-z0-9_]/gi, "_");
                const score = ev.score != null ? `<span class="text-[10px] font-mono" style="color:var(--st-success)">score ${Number(ev.score).toFixed(2)}</span>` : "";
                const tag = `<span class="src-tag src-tag-${escapeHtml(safeSrc)}">${escapeHtml(src)}</span>`;
                const type = ev.type ? `<span class="text-slate-600 text-[11px]">${escapeHtml(ev.type)}</span>` : "";
                return `<div class="key-signal-item">
                    <div class="flex items-center gap-2 mb-1">${tag}${type}${score}</div>
                    <div class="text-slate-800">${escapeHtml(ev.summary || "(无摘要)")}</div>
                </div>`;
            }).join("");
            parts.push(`<div class="key-signal-card"><div class="key-signal-title">根因候选 + 高分支撑证据</div>${items}</div>`);
        }

        // Runbook 引用面: 从 source=runbook 的 evidence 里提取 SOP 标题, 让 SRE 知道这次诊断引用了哪些 Runbook
        const runbookEvs = evidence.filter((e) => e.source === "runbook");
        if (runbookEvs.length > 0) {
            const chips = runbookEvs.map((ev) => {
                const title = ev.summary || ev.type || (ev.metadata && ev.metadata.title) || "(未命名 Runbook)";
                return `<span class="runbook-ref" title="${escapeHtml(ev.type || "")}">${escapeHtml(String(title).slice(0, 80))}</span>`;
            }).join("");
            parts.push(`<div class="inc-section-title">Runbook 引用 <span class="text-slate-400 font-normal">${runbookEvs.length}</span></div>
                <div>${chips}</div>`);
        }
    }

    // 证据链
    parts.push(`<div class="inc-section-title">证据链 <span class="text-slate-400 font-normal">${evidence.length} 条</span></div>`);
    if (evidence.length === 0) {
        parts.push(`<div class="text-slate-400 italic text-center py-3 border bg-slate-50">暂无证据</div>`);
    } else {
        const orderedSources = ["alert", "metric", "log", "trace", "mcp_tool_result", "runbook", "incident_history", "rca", "human_feedback"];
        const groups = {};
        evidence.forEach((e) => {
            const src = e.source || "unknown";
            (groups[src] = groups[src] || []).push(e);
        });
        const sourceKeys = orderedSources.filter((s) => groups[s]).concat(Object.keys(groups).filter((s) => !orderedSources.includes(s)));
        const cards = [];
        sourceKeys.forEach((src) => {
            groups[src].forEach((ev) => cards.push(renderEvidenceCard(ev)));
        });
        parts.push(`<div class="space-y-2">${cards.join("")}</div>`);
    }

    // Agent Runs
    if (agentRuns.length) {
        parts.push(`<div class="inc-section-title">Agent Runs <span class="text-slate-400 font-normal">${agentRuns.length}</span></div>`);
        const rows = agentRuns.map((run) => {
            const name = run.agent_name || run.name || run.role || "?";
            const tokens = run.total_tokens || run.tokens || (run.input_tokens != null ? (run.input_tokens + (run.output_tokens || 0)) : 0);
            return `<div class="flex items-center gap-2 px-2 py-1.5 border bg-slate-50 text-xs">
                <span class="font-mono font-semibold text-slate-700 truncate">${escapeHtml(name)}</span>
                ${renderStatusBadge(run.status)}
                ${tokens ? `<span class="text-slate-500">${tokens} tok</span>` : ""}
                ${run.elapsed_ms != null ? `<span class="text-slate-400 ml-auto shrink-0">${run.elapsed_ms}ms</span>` : ""}
            </div>`;
        });
        parts.push(`<div class="space-y-1">${rows.join("")}</div>`);
    }

    // Tool Calls
    if (toolCalls.length) {
        parts.push(`<div class="inc-section-title">工具调用 <span class="text-slate-400 font-normal">${toolCalls.length}</span></div>`);
        const rows = toolCalls.map((tc) => {
            const statusStr = (tc.status || "").toLowerCase();
            const ok = tc.success === true || tc.ok === true || statusStr === "succeeded" || statusStr === "ok" || statusStr === "success";
            const icon = ok ? "✓" : "✗";
            const color = ok ? "text-emerald-600" : "text-rose-600";
            const name = tc.tool_name || tc.name || "?";
            return `<div class="flex items-center gap-2 px-2 py-1 border bg-slate-50 text-xs">
                <span class="${color} font-semibold">${icon}</span>
                <span class="font-mono text-slate-700 truncate">${escapeHtml(name)}</span>
                ${tc.elapsed_ms != null ? `<span class="text-slate-400 ml-auto shrink-0">${tc.elapsed_ms}ms</span>` : ""}
            </div>`;
        });
        parts.push(`<div class="space-y-1">${rows.join("")}</div>`);
    }

    detail.innerHTML = parts.join("");

    // 复制按钮事件 (避免 inline onclick 在严格 CSP 下失效)
    detail.querySelectorAll("[data-inc-copy]").forEach((btn) => {
        btn.addEventListener("click", () => {
            const val = btn.dataset.incCopy || "";
            if (!val) return;
            navigator.clipboard?.writeText(val).then(() => {
                const orig = btn.textContent;
                btn.textContent = "已复制 ✓";
                setTimeout(() => { btn.textContent = orig; }, 1200);
            });
        });
    });
    detail.querySelectorAll("[data-inc-delete]").forEach((btn) => {
        btn.addEventListener("click", async () => {
            const taskId = btn.dataset.incDelete || "";
            if (!taskId) return;
            if (!confirm("确认删除这条事件历史？关联的报告、证据和执行记录也会删除。")) return;
            btn.disabled = true;
            btn.textContent = "删除中...";
            try {
                const r = await fetch(`${API}/incidents/tasks/${encodeURIComponent(taskId)}`, {
                    method: "DELETE",
                });
                const data = await r.json().catch(() => null);
                if (!r.ok) throw new Error(data?.detail || `HTTP ${r.status}`);
                incidents.selectedId = null;
                incidents.selectedIds.delete(taskId);
                detail.innerHTML = `<div class="text-center text-slate-400 italic py-8">事件已删除，请从左侧选择其他任务</div>`;
                await loadIncidents();
            } catch (e) {
                alert(`删除失败: ${e.message}`);
                btn.disabled = false;
                btn.textContent = "删除";
            }
        });
    });
}

function renderEvidenceCard(ev) {
    const src = ev.source || "unknown";
    const safeSrc = String(src).replace(/[^a-z0-9_]/gi, "_");
    const score = ev.score != null ? `<span class="text-emerald-600 text-[10px]">score ${Number(ev.score).toFixed(2)}</span>` : "";
    const contentJson = ev.content && typeof ev.content === "object" && Object.keys(ev.content).length
        ? JSON.stringify(ev.content, null, 2)
        : "";
    const occurred = ev.occurred_at || ev.created_at || "";
    return `<div class="evidence-card src-${escapeHtml(safeSrc)}">
        <div class="ev-header">
            <span class="src-tag src-tag-${escapeHtml(safeSrc)}">${escapeHtml(src)}</span>
            <span class="text-slate-700 font-medium text-[11px]">${escapeHtml(ev.type || "")}</span>
            ${score}
            <span class="text-slate-400 text-[10px] ml-auto">${escapeHtml(occurred)}</span>
        </div>
        <div class="text-slate-700">${escapeHtml(ev.summary || "(无摘要)")}</div>
        ${contentJson ? `<details class="mt-1"><summary class="text-[10px] text-slate-500 cursor-pointer hover:text-indigo-600">查看原始 content</summary><pre class="ev-content">${escapeHtml(contentJson)}</pre></details>` : ""}
    </div>`;
}

function renderStatusBadge(status) {
    const map = {
        pending: "排队",
        running: "运行中",
        succeeded: "成功",
        failed: "失败",
        cancelled: "已取消",
        timeout: "超时",
    };
    const label = map[status] || status || "未知";
    const valid = ["pending", "running", "succeeded", "failed", "cancelled"];
    const cls = valid.includes(status) ? `inc-badge-${status}` : "inc-badge-unknown";
    return `<span class="inc-badge ${cls}">${escapeHtml(label)}</span>`;
}

function renderSevDot(severity) {
    const s = String(severity || "").toLowerCase();
    let cls = "sev-unknown";
    if (s.includes("critical") || s === "high" || s === "p0" || s === "p1") cls = "sev-critical";
    else if (s.includes("warn") || s === "medium" || s === "p2")              cls = "sev-warning";
    else if (s.includes("info") || s === "low" || s === "p3")                 cls = "sev-info";
    return `<span class="sev-dot ${cls}" title="${escapeHtml(severity || "")}"></span>`;
}

function timeAgo(iso) {
    if (!iso) return "—";
    const t = new Date(iso).getTime();
    if (!t || isNaN(t)) return "—";
    const diff = (Date.now() - t) / 1000;
    if (diff < 0) return "刚刚";
    if (diff < 60) return `${Math.floor(diff)} 秒前`;
    if (diff < 3600) return `${Math.floor(diff / 60)} 分钟前`;
    if (diff < 86400) return `${Math.floor(diff / 3600)} 小时前`;
    return `${Math.floor(diff / 86400)} 天前`;
}

function formatDuration(startIso, endIso) {
    if (!startIso || !endIso) return "—";
    const ms = new Date(endIso).getTime() - new Date(startIso).getTime();
    if (isNaN(ms) || ms < 0) return "—";
    if (ms < 1000) return `${ms}ms`;
    if (ms < 60000) return `${(ms / 1000).toFixed(1)}s`;
    const m = Math.floor(ms / 60000);
    const s = Math.floor((ms % 60000) / 1000);
    return `${m}m ${s}s`;
}

async function deleteSelectedIncidents() {
    if (incidents.bulkDeleting || incidents.selectedIds.size === 0) return;
    const taskIds = [...incidents.selectedIds];
    if (!confirm(`确认删除选中的 ${taskIds.length} 条事件历史？关联的报告、证据和执行记录也会删除。`)) return;

    incidents.bulkDeleting = true;
    syncIncidentBulkControls();
    try {
        const r = await fetch(`${API}/incidents/tasks/bulk-delete`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ task_ids: taskIds }),
        });
        const data = await r.json().catch(() => null);
        if (!r.ok) throw new Error(data?.detail || `HTTP ${r.status}`);

        const deletedIds = new Set((data?.items || []).map((item) => item.task_id));
        taskIds.forEach((taskId) => incidents.selectedIds.delete(taskId));
        if (incidents.selectedId && deletedIds.has(incidents.selectedId)) {
            incidents.selectedId = null;
            const detail = document.getElementById("inc-detail");
            if (detail) {
                detail.innerHTML = `<div class="text-center text-slate-400 italic py-8">已批量删除 ${data.deleted || deletedIds.size} 条事件，请从左侧选择其他任务</div>`;
            }
        }
        await loadIncidents();

        const skipped = data?.skipped_active?.length || 0;
        const missing = data?.not_found?.length || 0;
        if (skipped || missing) {
            alert(`已删除 ${data.deleted || 0} 条；跳过进行中 ${skipped} 条；未找到 ${missing} 条。`);
        }
    } catch (e) {
        alert(`批量删除失败: ${e.message}`);
    } finally {
        incidents.bulkDeleting = false;
        syncIncidentBulkControls();
    }
}

// 过滤 chip / 搜索 / 刷新 / 自动开关 事件绑定
document.querySelectorAll("[data-inc-status]").forEach((btn) => {
    btn.addEventListener("click", () => {
        document.querySelectorAll("[data-inc-status]").forEach((b) => b.classList.remove("inc-chip-active"));
        btn.classList.add("inc-chip-active");
        incidents.filterStatus = btn.dataset.incStatus || "all";
        renderIncidentList();
    });
});
const incSearchEl = document.getElementById("inc-search");
if (incSearchEl) {
    incSearchEl.addEventListener("input", (e) => {
        incidents.search = e.target.value || "";
        renderIncidentList();
    });
}
const incRefreshEl = document.getElementById("inc-refresh");
if (incRefreshEl) {
    incRefreshEl.addEventListener("click", () => loadIncidents());
}
const incAutoEl = document.getElementById("inc-auto");
if (incAutoEl) {
    incAutoEl.addEventListener("change", (e) => {
        incidents.auto = !!e.target.checked;
        incScheduleAutoRefresh();
    });
}
const incSelectAllEl = document.getElementById("inc-select-all");
if (incSelectAllEl) {
    incSelectAllEl.addEventListener("change", (e) => {
        getFilteredIncidentItems().filter(isIncidentDeletable).forEach((task) => {
            if (e.target.checked) incidents.selectedIds.add(task.id);
            else incidents.selectedIds.delete(task.id);
        });
        renderIncidentList();
    });
}
const incBulkDeleteEl = document.getElementById("inc-bulk-delete");
if (incBulkDeleteEl) {
    incBulkDeleteEl.addEventListener("click", deleteSelectedIncidents);
}

// ============================================================
// 文档管理
// ============================================================
const uploadZone = document.getElementById("upload-zone");
const uploadInput = document.getElementById("upload-input");
const uploadResult = document.getElementById("upload-result");
const KB_ADMIN_TOKEN_KEY = "multi_agent_kb_admin_token";

uploadZone.addEventListener("click", () => uploadInput.click());
uploadInput.addEventListener("change", () => uploadInput.files[0] && uploadFile(uploadInput.files[0]));
uploadZone.addEventListener("dragover", (e) => { e.preventDefault(); uploadZone.classList.add("upload-dragover"); });
uploadZone.addEventListener("dragleave", () => uploadZone.classList.remove("upload-dragover"));
uploadZone.addEventListener("drop", (e) => {
    e.preventDefault();
    uploadZone.classList.remove("upload-dragover");
    if (e.dataTransfer.files[0]) uploadFile(e.dataTransfer.files[0]);
});
document.getElementById("docs-refresh").addEventListener("click", loadDocs);

async function uploadFile(file) {
    uploadResult.innerHTML = `<div style="color:var(--accent)">上传 ${escapeHtml(file.name)} ...</div>`;
    const formData = new FormData();
    formData.append("file", file);
    try {
        const r = await fetch(`${API}/documents/upload`, {
            method: "POST",
            headers: { "X-KB-Admin-Token": getKbAdminToken() },
            body: formData,
        });
        const data = await r.json().catch(() => null);
        if (!r.ok) {
            if (r.status === 401 || r.status === 403) sessionStorage.removeItem(KB_ADMIN_TOKEN_KEY);
            throw new Error(data?.detail || data?.message || `HTTP ${r.status}`);
        }
        if (data.code === "SUCCESS") {
            uploadResult.innerHTML = `<div class="text-emerald-600">✓ 已索引 ${data.data.chunks_indexed} 个 chunk (${data.data.bytes} bytes)</div>`;
            loadDocs();
        } else {
            uploadResult.innerHTML = `<div class="text-red-500">✗ ${escapeHtml(data?.message || "上传失败")}</div>`;
        }
    } catch (e) {
        uploadResult.innerHTML = `<div class="text-red-500">✗ ${escapeHtml(e.message)}</div>`;
    }
}

async function loadDocs() {
    const listEl = document.getElementById("docs-list");
    listEl.innerHTML = '<span class="text-sm text-slate-400 italic">加载中...</span>';
    try {
        const r = await fetch(`${API}/documents`);
        const data = await r.json();
        const docs = data?.data?.documents || [];
        if (docs.length === 0) {
            listEl.innerHTML = '<span class="text-sm text-slate-400 italic">暂无文档, 请先上传</span>';
            return;
        }
        listEl.innerHTML = "";
        docs.forEach((d) => {
            const div = document.createElement("div");
            div.className = "doc-card";
            div.innerHTML = `
                <div>
                    <div class="font-semibold text-sm">${escapeHtml(d.source)}</div>
                    <div class="text-xs text-slate-500">${d.chunk_count} 个 chunk</div>
                </div>
                <button class="text-red-500 hover:text-red-700 text-sm" data-source="${escapeHtml(d.source)}">删除</button>
            `;
            div.querySelector("button").addEventListener("click", (e) => {
                if (confirm(`确认删除 ${d.source}?`)) deleteDoc(d.source);
            });
            listEl.appendChild(div);
        });
    } catch (e) {
        listEl.innerHTML = `<span class="text-red-500">加载失败: ${e.message}</span>`;
    }
}

async function deleteDoc(source) {
    try {
        const r = await fetch(`${API}/documents/${encodeURIComponent(source)}`, {
            method: "DELETE",
            headers: { "X-KB-Admin-Token": getKbAdminToken() },
        });
        const data = await r.json().catch(() => null);
        if (!r.ok || data?.code !== "SUCCESS") {
            if (r.status === 401 || r.status === 403) sessionStorage.removeItem(KB_ADMIN_TOKEN_KEY);
            throw new Error(data?.detail || data?.message || `HTTP ${r.status}`);
        }
        loadDocs();
    } catch (e) {
        alert(`删除失败: ${e.message}`);
    }
}

function getKbAdminToken() {
    let token = sessionStorage.getItem(KB_ADMIN_TOKEN_KEY) || "";
    if (!token) {
        token = prompt("请输入知识库管理员 Token") || "";
        token = token.trim();
        if (!token) throw new Error("未输入管理员 Token");
        sessionStorage.setItem(KB_ADMIN_TOKEN_KEY, token);
    }
    return token;
}

// ============================================================
// 工具函数
// ============================================================
async function consumeSSE(response, onEvent) {
    if (!response.ok) {
        const text = await response.text().catch(() => "");
        throw new Error(`HTTP ${response.status}: ${text.slice(0, 200)}`);
    }
    if (!response.body) {
        throw new Error("浏览器不支持 ReadableStream");
    }

    const reader = response.body.getReader();
    const decoder = new TextDecoder("utf-8");
    let buffer = "";

    // SSE 标准支持 \r\n / \n / \r 三种分隔, 这里全兼容
    const blockSplit = /\r?\n\r?\n|\n\n/;
    const lineSplit = /\r?\n/;

    while (true) {
        const { done, value } = await reader.read();
        if (done) {
            // 处理最后剩下的 buffer
            if (buffer.trim()) parseBlock(buffer);
            break;
        }
        buffer += decoder.decode(value, { stream: true });

        // 切出所有完整的 event block
        let parts = buffer.split(blockSplit);
        buffer = parts.pop();  // 最后一段可能不完整, 留到下次
        for (const block of parts) parseBlock(block);
    }

    function parseBlock(block) {
        for (const line of block.split(lineSplit)) {
            if (line.startsWith("data:")) {
                const payload = line.slice(5).trim();
                if (!payload) continue;
                try {
                    onEvent(JSON.parse(payload));
                } catch (e) {
                    console.warn("[SSE] JSON parse error:", payload, e);
                }
            }
        }
    }
}

function escapeHtml(s) {
    if (s == null) return "";
    return String(s)
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;");
}

// 极简 Markdown -> HTML (够用即可, 不引第三方库)
function renderMarkdown(md) {
    if (!md) return "";
    // 处理 LLM 偶尔输出 \n 字面量 (而非实际换行) 的 bug
    // (\\\\n 在 JS 字符串里就是 \n 两个字符, 把它替换成真换行)
    let s = String(md).replace(/\\n/g, "\n").replace(/\\t/g, "\t");
    let h = escapeHtml(s);
    // 代码块
    h = h.replace(/```([\s\S]*?)```/g, (_, code) => `<pre><code>${code}</code></pre>`);
    // 行内代码
    h = h.replace(/`([^`\n]+)`/g, "<code>$1</code>");
    // 标题
    h = h.replace(/^### (.+)$/gm, "<h3>$1</h3>");
    h = h.replace(/^## (.+)$/gm, "<h2>$1</h2>");
    h = h.replace(/^# (.+)$/gm, "<h1>$1</h1>");
    // 加粗
    h = h.replace(/\*\*([^*]+)\*\*/g, "<strong>$1</strong>");
    // 列表
    h = h.replace(/^[\-\*] (.+)$/gm, "<li>$1</li>");
    h = h.replace(/(<li>[\s\S]*?<\/li>)(\n<li>)/g, "$1$2");
    h = h.replace(/(<li>[\s\S]+?<\/li>)/g, (m) => `<ul>${m}</ul>`);
    h = h.replace(/<\/ul>\s*<ul>/g, "");
    // 段落
    h = h.replace(/\n\n/g, "</p><p>");
    h = h.replace(/\n/g, "<br>");
    return `<p>${h}</p>`;
}

// 渲染 wiki markdown: 在普通 markdown 基础上把 [[category/slug]] 渲染成可点击 chip
function renderWikiMarkdown(md) {
    if (!md) return "";
    const html = renderMarkdown(md);
    return html.replace(/\[\[([a-z0-9_\-]+)\/([a-z0-9_\-]+)\]\]/gi, (_, cat, slug) =>
        `<a class="wikilink" data-wiki-ref="${escapeHtml(cat)}/${escapeHtml(slug)}">[[${escapeHtml(cat)}/${escapeHtml(slug)}]]</a>`
    );
}

// ============================================================
// 经验库 (Wiki) Tab 控制器
// ============================================================
const wiki = { pages: [], selectedRef: null, cat: "all", loaded: false };

async function wikiOnTabEnter() {
    if (wiki.loaded) return;
    wiki.loaded = true;
    await Promise.all([loadWikiOverview(), loadWikiPages(), loadWikiLog()]);
}

async function loadWikiOverview() {
    const line = document.getElementById("wiki-overview-line");
    try {
        const r = await fetch(`${API}/wiki/overview`);
        const data = await r.json();
        if (!data.enabled) {
            line.textContent = "Wiki 未启用 (WIKI_ENABLED=False)";
            return;
        }
        const pages = data.pages || {};
        line.textContent = `${(pages.patterns || 0)} 个故障模式 · ${(pages.services || 0)} 个服务页 · ${data.recall_enabled ? "召回开启" : "召回关闭"}`;
    } catch (e) {
        line.textContent = `加载失败: ${e.message}`;
    }
}

async function loadWikiPages() {
    const el = document.getElementById("wiki-pages");
    try {
        const r = await fetch(`${API}/wiki/pages?limit=300`);
        const data = await r.json();
        wiki.pages = data.items || [];
        renderWikiPageList();
    } catch (e) {
        el.innerHTML = `<span class="text-rose-500">加载失败: ${escapeHtml(e.message)}</span>`;
    }
}

function renderWikiPageList() {
    const el = document.getElementById("wiki-pages");
    if (!el) return;
    const filtered = wiki.pages.filter((p) => wiki.cat === "all" || p.category === wiki.cat);
    if (!filtered.length) {
        el.innerHTML = `<div class="text-slate-400 italic text-center py-6">无 wiki 页 (跑一次诊断自动 ingest)</div>`;
        return;
    }
    el.innerHTML = "";
    filtered.forEach((p) => {
        const card = document.createElement("div");
        card.className = `wiki-page-card ${wiki.selectedRef === p.ref ? "selected" : ""}`;
        card.dataset.ref = p.ref;
        const catTag = `<span class="wiki-cat-tag wiki-cat-${p.category}">${p.category}</span>`;
        const modified = p.modified_at ? timeAgo(p.modified_at) : "";
        card.innerHTML = `
            <div class="flex items-center gap-1 mb-0.5">
                ${catTag}
                <span class="font-semibold text-slate-700 truncate">${escapeHtml(p.slug)}</span>
            </div>
            <div class="text-slate-500 text-[11px] truncate">${escapeHtml(p.preview || "(空页)")}</div>
            <div class="text-slate-400 text-[10px] mt-0.5">${modified}</div>`;
        card.addEventListener("click", () => loadWikiPage(p.category, p.slug));
        el.appendChild(card);
    });
}

async function loadWikiPage(category, slug) {
    const ref = `${category}/${slug}`;
    wiki.selectedRef = ref;
    document.querySelectorAll(".wiki-page-card").forEach((c) => c.classList.toggle("selected", c.dataset.ref === ref));
    setText("wiki-page-title", ref);
    setText("wiki-page-meta", "");
    const content = document.getElementById("wiki-page-content");
    content.innerHTML = `<div class="text-slate-400 italic text-center py-8">加载中...</div>`;
    try {
        const r = await fetch(`${API}/wiki/pages/${encodeURIComponent(category)}/${encodeURIComponent(slug)}`);
        if (!r.ok) throw new Error(`HTTP ${r.status}`);
        const data = await r.json();
        content.innerHTML = renderWikiMarkdown(data.content || "");
        setText("wiki-page-meta", `${data.size_bytes || 0} bytes · ${timeAgo(data.modified_at)}`);
        // 给所有 wikilink 接点击 → 跳转
        content.querySelectorAll(".wikilink").forEach((a) => {
            a.addEventListener("click", (e) => {
                e.preventDefault();
                const refStr = a.dataset.wikiRef || "";
                const [cat2, slug2] = refStr.split("/");
                if (cat2 && slug2) loadWikiPage(cat2, slug2);
            });
        });
    } catch (e) {
        content.innerHTML = `<div class="text-rose-500">加载失败: ${escapeHtml(e.message)}</div>`;
    }
}

async function loadWikiLog() {
    const el = document.getElementById("wiki-log");
    try {
        const r = await fetch(`${API}/wiki/log?limit=30`);
        const data = await r.json();
        const items = data.items || [];
        if (!items.length) {
            el.innerHTML = `<span class="italic">暂无 ingest 流水</span>`;
            return;
        }
        el.innerHTML = items.map((e) =>
            `<div><span class="text-indigo-500">${escapeHtml(e.date)}</span> ${escapeHtml(e.entry)}</div>`
        ).join("");
    } catch (e) {
        el.innerHTML = `<span class="text-rose-500">加载失败</span>`;
    }
}

// wiki cat 切换 & 刷新按钮
document.querySelectorAll("[data-wiki-cat]").forEach((btn) => {
    btn.addEventListener("click", () => {
        document.querySelectorAll("[data-wiki-cat]").forEach((b) => b.classList.remove("inc-chip-active"));
        btn.classList.add("inc-chip-active");
        wiki.cat = btn.dataset.wikiCat || "all";
        renderWikiPageList();
    });
});
const wikiRefreshBtn = document.getElementById("wiki-refresh");
if (wikiRefreshBtn) {
    wikiRefreshBtn.addEventListener("click", () => {
        wiki.loaded = false;
        wikiOnTabEnter();
    });
}

// ============================================================
// 评估面板 (Documents Tab 内嵌)
// ============================================================
const evalState = { items: [], selectedName: null };

async function loadEvalReports() {
    const list = document.getElementById("eval-list");
    if (!list) return;
    try {
        const r = await fetch(`${API}/eval/reports?limit=30`);
        const data = await r.json();
        evalState.items = data.items || [];
        if (!evalState.items.length) {
            list.innerHTML = `<div class="text-slate-400 italic text-xs">${data.note || "暂无报告"}</div>`;
            return;
        }
        list.innerHTML = "";
        evalState.items.forEach((rep) => {
            const card = document.createElement("div");
            card.className = `eval-card ${evalState.selectedName === rep.name ? "selected" : ""}`;
            card.dataset.name = rep.name;
            const s = rep.summary || {};
            let metrics = "";
            if (rep.mode === "retrieval") {
                const tags = [
                    `hit@${s.k || "?"}=${(s.hit_at_k != null ? s.hit_at_k.toFixed(3) : "—")}`,
                    `mrr=${(s.mrr_at_k != null ? s.mrr_at_k.toFixed(3) : "—")}`,
                    `recall=${(s.recall_at_k != null ? s.recall_at_k.toFixed(3) : "—")}`,
                ];
                metrics = tags.map((t) => `<span class="eval-metric">${escapeHtml(t)}</span>`).join("");
            } else if (rep.mode === "ragas") {
                const tags = [
                    `faith=${(s.faithfulness != null ? s.faithfulness.toFixed(3) : "—")}`,
                    `rel=${(s.answer_relevancy != null ? s.answer_relevancy.toFixed(3) : "—")}`,
                    `cprec=${(s.context_precision != null ? s.context_precision.toFixed(3) : "—")}`,
                    `crecall=${(s.context_recall != null ? s.context_recall.toFixed(3) : "—")}`,
                ];
                metrics = tags.map((t) => `<span class="eval-metric">${escapeHtml(t)}</span>`).join("");
            }
            card.innerHTML = `
                <div class="flex items-center justify-between mb-1">
                    <span class="font-semibold text-slate-700 uppercase text-[10px] tracking-wider">${escapeHtml(rep.mode)}</span>
                    <span class="text-[10px] text-slate-400">${escapeHtml(rep.generated_at || "")}</span>
                </div>
                <div class="text-[10px] text-slate-400 mb-1">${rep.summary?.rows || 0} 题 · ${(rep.summary?.elapsed_sec || 0).toFixed(1)}s</div>
                <div>${metrics}</div>`;
            card.addEventListener("click", () => loadEvalReport(rep.name));
            list.appendChild(card);
        });
    } catch (e) {
        list.innerHTML = `<div class="text-rose-500 text-xs">加载失败: ${escapeHtml(e.message)}</div>`;
    }
}

async function loadEvalReport(name) {
    evalState.selectedName = name;
    document.querySelectorAll(".eval-card").forEach((c) => c.classList.toggle("selected", c.dataset.name === name));
    const detail = document.getElementById("eval-detail");
    detail.innerHTML = `<div class="text-slate-400 italic">加载中...</div>`;
    try {
        const r = await fetch(`${API}/eval/reports/${encodeURIComponent(name)}`);
        const data = await r.json();
        let html = `<div class="font-semibold text-slate-700 mb-2">${escapeHtml(name)}</div>`;
        html += `<div class="text-slate-500 mb-3">mode=${data.mode} · 题量=${data.rows} · 用时=${(data.elapsed_sec || 0).toFixed(1)}s · 明细 ${data.details_count} 条</div>`;
        if (data.mode === "retrieval") {
            const metrics = [
                ["hit_at_k", data.hit_at_k],
                ["mrr_at_k", data.mrr_at_k],
                ["recall_at_k", data.recall_at_k],
            ];
            html += `<div class="space-y-1 mb-3">${metrics.map(([k, v]) => `<div>${k}: <span class="font-mono font-semibold ${gradeClass(v)}">${formatScore(v)}</span></div>`).join("")}</div>`;
            html += `<div class="text-slate-500 mb-2">配置: hybrid=${data.hybrid} · rerank=${data.rerank} · retrieve_k=${data.retrieve_k} · bm25_w=${data.bm25_weight} · rrf_k=${data.rrf_k}</div>`;
        } else if (data.mode === "ragas") {
            const av = data.averages || {};
            const oe = data.openevals_averages || {};
            const all = { ...av, ...oe };
            html += `<div class="grid grid-cols-2 gap-2 mb-3">${Object.entries(all).map(([k, v]) => `<div>${k}: <span class="font-mono font-semibold ${gradeClass(v)}">${formatScore(v)}</span></div>`).join("")}</div>`;
        }
        html += `<button id="eval-low" class="mt-2 px-3 py-1 text-xs text-white" style="background:var(--accent)">查看低分题</button>`;
        html += `<div id="eval-low-list" class="mt-3"></div>`;
        detail.innerHTML = html;
        const lowBtn = document.getElementById("eval-low");
        if (lowBtn) lowBtn.addEventListener("click", () => loadEvalLowScores(name, data.mode));
    } catch (e) {
        detail.innerHTML = `<div class="text-rose-500">加载失败: ${escapeHtml(e.message)}</div>`;
    }
}

async function loadEvalLowScores(name, mode) {
    const listEl = document.getElementById("eval-low-list");
    if (!listEl) return;
    listEl.innerHTML = `<div class="text-slate-400 italic text-xs">加载低分题...</div>`;
    const metric = mode === "ragas" ? "faithfulness" : "hit";
    try {
        const r = await fetch(`${API}/eval/reports/${encodeURIComponent(name)}/low-scores?metric=${metric}&threshold=0.5&limit=20`);
        const data = await r.json();
        const items = data.items || [];
        if (!items.length) {
            listEl.innerHTML = `<div class="text-emerald-600 text-xs">✓ 没有低于 0.5 的样本, 整体表现良好</div>`;
            return;
        }
        const rows = items.map((it) => {
            const q = it.question || it.query || "";
            const sc = typeof it.score === "object" ? JSON.stringify(it.score) : String(it.score);
            return `<div class="border-l-2 border-rose-400 pl-2 py-1">
                <div class="text-slate-700 font-medium text-[11px]">[${escapeHtml(String(it.scenario || ""))}] ${escapeHtml(q.slice(0, 120))}</div>
                <div class="text-rose-600 text-[10px] font-mono">score: ${escapeHtml(sc)}</div>
                ${it.answer ? `<div class="text-slate-500 text-[10px] mt-0.5">answer: ${escapeHtml(it.answer)}</div>` : ""}
            </div>`;
        }).join("");
        listEl.innerHTML = `<div class="space-y-1.5 max-h-[260px] overflow-y-auto">${rows}</div>`;
    } catch (e) {
        listEl.innerHTML = `<div class="text-rose-500 text-xs">加载失败: ${escapeHtml(e.message)}</div>`;
    }
}

function formatScore(v) {
    if (v == null) return "—";
    if (typeof v !== "number") return String(v);
    return v.toFixed(3);
}

function gradeClass(v) {
    if (v == null || typeof v !== "number") return "";
    if (v >= 0.8) return "text-emerald-700";
    if (v >= 0.5) return "text-amber-700";
    return "text-rose-700";
}

const evalRefreshBtn = document.getElementById("eval-refresh");
if (evalRefreshBtn) evalRefreshBtn.addEventListener("click", loadEvalReports);

// ============================================================
// 审批 (Approval) Inbox
// ============================================================
const approvals = { items: [], available: true, pollTimer: null };

async function loadApprovals() {
    try {
        const r = await fetch(`${API}/approvals/pending?limit=50`);
        const data = await r.json();
        approvals.items = data.items || [];
        approvals.available = data.available !== false;
        renderApprovalBell();
        renderApprovalList();
    } catch (e) {
        approvals.available = false;
        renderApprovalBell();
    }
}

function renderApprovalBell() {
    const bell = document.getElementById("approval-bell");
    const badge = document.getElementById("approval-badge");
    if (!bell || !badge) return;
    if (!approvals.available) {
        bell.classList.add("hidden");
        return;
    }
    bell.classList.remove("hidden");
    const n = approvals.items.length;
    if (n > 0) {
        badge.classList.remove("hidden");
        badge.textContent = String(n);
        bell.classList.add("has-pending");   // 静态红色强调, 取代抖动
    } else {
        badge.classList.add("hidden");
        bell.classList.remove("has-pending");
    }
}

function renderApprovalList() {
    const el = document.getElementById("approval-list");
    if (!el) return;
    const items = approvals.items || [];
    if (!items.length) {
        el.innerHTML = `<div class="text-slate-400 italic text-center py-6">无待审批请求</div>`;
        return;
    }
    el.innerHTML = "";
    items.forEach((a) => {
        const card = document.createElement("div");
        card.className = "approval-card";
        const argsPreview = a.tool_args && Object.keys(a.tool_args).length
            ? `<pre class="bg-white/60 border border-amber-200 rounded p-1.5 text-[10px] font-mono mt-1 max-h-32 overflow-auto whitespace-pre-wrap break-all">${escapeHtml(JSON.stringify(a.tool_args, null, 2))}</pre>`
            : "";
        card.innerHTML = `
            <div class="flex items-center justify-between mb-1">
                <span class="approval-tool">${escapeHtml(a.tool_name || "?")}</span>
                <span class="text-[10px] text-amber-700">${timeAgo(a.created_at)} · expires ${escapeHtml(a.expires_at || "")}</span>
            </div>
            <div class="text-amber-900 text-[11px] mb-1">${escapeHtml(a.reason || "(无原因)")}</div>
            ${a.impact_summary ? `<div class="text-[10px] text-amber-700 mb-1">影响: ${escapeHtml(a.impact_summary)}</div>` : ""}
            ${a.task_id ? `<div class="text-[10px] text-slate-500 font-mono">task: ${escapeHtml(a.task_id)}</div>` : ""}
            ${argsPreview}
            <div class="approval-actions">
                <button data-approve="${escapeHtml(a.id)}" class="approval-btn approval-btn-allow">批准 ✓</button>
                <button data-deny="${escapeHtml(a.id)}" class="approval-btn approval-btn-deny">拒绝 ✗</button>
            </div>`;
        el.appendChild(card);
    });
    el.querySelectorAll("[data-approve]").forEach((b) => b.addEventListener("click", () => decideApproval(b.dataset.approve, "approved")));
    el.querySelectorAll("[data-deny]").forEach((b) => b.addEventListener("click", () => decideApproval(b.dataset.deny, "denied")));
}

async function decideApproval(reqId, decision) {
    const reason = decision === "denied" ? (prompt("拒绝原因 (可空)") || "") : "";
    try {
        const r = await fetch(`${API}/approvals/${encodeURIComponent(reqId)}/decide`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ decision, decided_by: "web-user", reason }),
        });
        if (!r.ok) {
            const txt = await r.text().catch(() => "");
            throw new Error(`HTTP ${r.status}: ${txt.slice(0, 120)}`);
        }
        await loadApprovals();
    } catch (e) {
        alert(`决策失败: ${e.message}`);
    }
}

// 铃 / 关闭 / 手动刷新 事件
const bellEl = document.getElementById("approval-bell");
const panelEl = document.getElementById("approval-panel");
const panelCloseEl = document.getElementById("approval-close");
const panelRefreshEl = document.getElementById("approval-refresh");
if (bellEl) {
    bellEl.addEventListener("click", () => {
        if (!panelEl) return;
        panelEl.classList.toggle("hidden");
        if (!panelEl.classList.contains("hidden")) loadApprovals();
    });
}
if (panelCloseEl) panelCloseEl.addEventListener("click", () => panelEl?.classList.add("hidden"));
if (panelRefreshEl) panelRefreshEl.addEventListener("click", loadApprovals);

// 全局轮询 (每 10s, 比 incidents 慢, 因为不在所有 tab 都重要)
function startApprovalPolling() {
    if (approvals.pollTimer) clearInterval(approvals.pollTimer);
    approvals.pollTimer = setInterval(loadApprovals, 10000);
    loadApprovals();
}
startApprovalPolling();

// ============================================================
// Chat → Incident 升级按钮
// ============================================================
const chatEscalateBtn = document.getElementById("chat-escalate");
if (chatEscalateBtn) {
    chatEscalateBtn.addEventListener("click", async () => {
        let query = (chatInput.value || "").trim();
        if (!query) {
            // 用最近一条用户消息作为升级内容
            const lastUser = Array.from(document.querySelectorAll("#chat-messages .chat-msg.user")).pop();
            query = lastUser ? lastUser.textContent.trim() : "";
        }
        if (!query) {
            alert("先在输入框写一句话, 或先提问过一次再点升级");
            return;
        }
        chatEscalateBtn.disabled = true;
        const origText = chatEscalateBtn.textContent;
        chatEscalateBtn.textContent = "升级中...";
        try {
            const r = await fetch(`${API}/incidents/from_chat`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    session_id: "web-chat",
                    query,
                    title: query.slice(0, 60),
                    severity: "warning",
                    diagnosis_mode: "fast",
                }),
            });
            if (!r.ok) {
                const txt = await r.text().catch(() => "");
                throw new Error(`HTTP ${r.status}: ${txt.slice(0, 200)}`);
            }
            const data = await r.json();
            chatEscalateBtn.textContent = `已升级 ✓ ${data.task_id}`;
            // 自动跳事件中心 + 选中新任务
            const incTab = document.querySelector('[data-tab="incidents"]');
            if (incTab) incTab.click();
            // 给 worker 写入流的几秒缓冲, 然后选中
            setTimeout(async () => {
                await loadIncidents();
                if (data.task_id) selectIncidentTask(data.task_id);
            }, 800);
        } catch (e) {
            chatEscalateBtn.textContent = "失败";
            alert(`升级失败: ${e.message}`);
        } finally {
            setTimeout(() => {
                chatEscalateBtn.disabled = false;
                chatEscalateBtn.textContent = origText;
            }, 2500);
        }
    });
}
