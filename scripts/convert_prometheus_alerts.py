"""把 awesome-prometheus-alerts 的 _data/rules.yml 转成 940+ 个独立 markdown.

每条告警生成一个 .md 文件, 结构:
  # {alert name}
  > Group / Service / Exporter / Severity
  ## 现象 (description)
  ## PromQL
  ## 持续时间 (for)
  ## 处理建议 (comments)

文件名: {NNNN}__{service_slug}__{alert_slug}.md
  - NNNN: 全局序号 (4 位补零, 保持顺序)
  - service_slug: 服务名 (空格替换为 -, 小写)
  - alert_slug: 告警名 (同上)

输出位置: data/kb_corpus/awesome-prometheus-alerts/

用法:
  python scripts/convert_prometheus_alerts.py
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / ".kb_clone_tmp" / "awesome-prometheus-alerts" / "_data" / "rules.yml"
OUT = ROOT / "data" / "kb_corpus" / "awesome-prometheus-alerts"


def slugify(text: str) -> str:
    """生成文件名安全的 slug."""
    s = text.lower().strip()
    s = re.sub(r"[^\w\s-]", "", s)  # 删除所有非 word/空格/横线的字符
    s = re.sub(r"[\s_-]+", "-", s)  # 空格/下划线/多个横线 -> 单个横线
    return s.strip("-")[:60]


def render_alert(group_name: str, service_name: str, exporter: str, rule: dict) -> str:
    """把一条 rule 渲染成 markdown."""
    name = rule.get("name", "Unknown alert")
    description = rule.get("description", "").strip()
    query = rule.get("query", "").strip()
    severity = rule.get("severity", "")
    for_dur = rule.get("for", "")
    comments = rule.get("comments", "").strip()

    lines = [
        f"# {name}",
        "",
        f"> Group: **{group_name}**  ",
        f"> Service: **{service_name}**  ",
        f"> Exporter: `{exporter}`  ",
        f"> Severity: **{severity}**" + (f"  \n> Duration (for): `{for_dur}`" if for_dur else ""),
        "",
        "## 现象 / Description",
        "",
        description or "_(no description)_",
        "",
        "## PromQL 查询",
        "",
        "```promql",
        query or "# (no query)",
        "```",
        "",
    ]

    if comments:
        lines += [
            "## 处理建议 / Comments",
            "",
            comments,
            "",
        ]

    lines += [
        "## 故障定位",
        "",
        f"- 触发该告警时, 检查 {service_name} 的相关指标和日志",
        f"- 严重等级: {severity}",
        f"- 来源: awesome-prometheus-alerts / {group_name} / {service_name}",
        "",
    ]

    return "\n".join(lines)


def main() -> None:
    if not SRC.exists():
        print(f"[error] 源文件不存在: {SRC}")
        print("       请先跑 scripts/fetch_kb_corpus.ps1 拉 repo")
        sys.exit(1)

    OUT.mkdir(parents=True, exist_ok=True)
    # 清空旧的 (避免残留旧的 awesome-prometheus-alerts_*.md)
    for f in OUT.glob("*.md"):
        f.unlink()

    print(f"[load] {SRC}")
    with SRC.open("r", encoding="utf-8") as fh:
        data = yaml.safe_load(fh)

    n_alert = 0
    n_group = 0
    n_service = 0
    seen_filenames: set[str] = set()

    for group in (data.get("groups") or []):
        n_group += 1
        gname = group.get("name", "Unknown group")
        for svc in (group.get("services") or []):
            n_service += 1
            sname = svc.get("name", "Unknown service")
            for exp in (svc.get("exporters") or []):
                exp_slug = exp.get("slug", "default")
                for rule in (exp.get("rules") or []):
                    n_alert += 1
                    aname = rule.get("name", f"alert-{n_alert}")

                    fname = f"{n_alert:04d}__{slugify(sname)}__{slugify(aname)}.md"
                    # 防 slug 撞车
                    while fname in seen_filenames:
                        fname = f"{n_alert:04d}_{len(seen_filenames)}__{slugify(sname)}__{slugify(aname)}.md"
                    seen_filenames.add(fname)

                    md = render_alert(gname, sname, exp_slug, rule)
                    (OUT / fname).write_text(md, encoding="utf-8")

    total_bytes = sum(f.stat().st_size for f in OUT.glob("*.md"))
    print(f"[done] groups={n_group}, services={n_service}, alerts={n_alert}")
    print(f"       output: {OUT}")
    print(f"       size:   {total_bytes/1024:.1f} KB")
    print(f"       avg:    {total_bytes/max(n_alert,1):.0f} bytes/file")


if __name__ == "__main__":
    main()
