"""把 loghub-2.0 的 *_templates.csv 转成知识库 .md (每数据集一篇)。

风格对齐 scripts/convert_prometheus_alerts.py: 离线把语料渲染成 .md, 再复用
scripts/ingest_kb_corpus.py 入 Milvus (它会自动扫 data/kb_corpus/**/*.md)。

为什么每个数据集一篇、而不是每条模板一个文件:
  - 单条模板是 `<*>` 占位符, 信息稀疏; 669 个碎文件检索噪声大、单文件信息量低;
  - 按数据集聚成一篇 (HDFS/Spark/BGL/OpenSSH/Apache), 每条模板配一条真实日志样例,
    检索时上下文更完整, 也更像一篇"该系统有哪些日志模式"的速查表。

输出: data/kb_corpus/log_templates/{dataset}_log_templates.md
loghub 原始数据在工作区顶层 data/raw/loghub2 (项目目录之外), 故默认 src 取 ROOT.parent。

用法:
  python scripts/convert_log_templates.py                 # 转换全部数据集
  python scripts/convert_log_templates.py --no-samples    # 不抓真实样例 (更快)
  python scripts/convert_log_templates.py --src /path/to/loghub2
  python scripts/convert_log_templates.py --dry-run       # 只统计, 不写文件

转换后入库:
  python scripts/ingest_kb_corpus.py            # log_templates/*.md 会被自动扫到
"""

from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

# 让 csv 能读 loghub 里偶发的超长行 (单条日志可能很长)
csv.field_size_limit(10 * 1024 * 1024)

ROOT = Path(__file__).resolve().parent.parent
# loghub 原始数据集在工作区顶层 (项目外): <workspace>/data/raw/loghub2
SRC_DEFAULT = ROOT.parent / "data" / "raw" / "loghub2"
OUT = ROOT / "data" / "kb_corpus" / "log_templates"

DATASETS = ["HDFS", "Spark", "BGL", "OpenSSH", "Apache"]


def _find_csv(src: Path, dataset: str, suffix: str) -> Path | None:
    """loghub 目录是 {DS}/{DS}/{DS}_full.log_{suffix}; 容错地找一下。"""
    candidates = [
        src / dataset / dataset / f"{dataset}_full.log_{suffix}",
        src / dataset / f"{dataset}_full.log_{suffix}",
    ]
    for c in candidates:
        if c.exists():
            return c
    # 兜底: 递归找第一个匹配
    hits = list(src.rglob(f"{dataset}_full.log_{suffix}"))
    return hits[0] if hits else None


def load_templates(path: Path) -> list[dict[str, str]]:
    """读 *_templates.csv -> [{EventId, EventTemplate, Occurrences}], 按出现次数降序。"""
    rows: list[dict[str, str]] = []
    with path.open("r", encoding="utf-8", newline="") as fh:
        for row in csv.DictReader(fh):
            rows.append(row)

    def _occ(r: dict[str, str]) -> int:
        try:
            return int(r.get("Occurrences") or 0)
        except Exception:
            return 0

    rows.sort(key=_occ, reverse=True)
    return rows


def collect_samples(path: Path | None, scan_lines: int) -> dict[str, str]:
    """从 *_structured.csv 前 scan_lines 行, 给每个 EventId 收一条真实日志样例。

    只扫前若干行: 高频模板基本都会在前面出现; 低频模板拿不到样例就只展示模板本身。
    避免全量扫 1.x G 的 structured.csv。
    """
    samples: dict[str, str] = {}
    if path is None or not path.exists():
        return samples
    with path.open("r", encoding="utf-8", newline="") as fh:
        reader = csv.DictReader(fh)
        for i, row in enumerate(reader):
            if i >= scan_lines:
                break
            eid = (row.get("EventId") or "").strip()
            if eid and eid not in samples:
                content = (row.get("Content") or "").strip()
                if content:
                    samples[eid] = content
    return samples


def render_dataset(dataset: str, templates: list[dict[str, str]], samples: dict[str, str]) -> str:
    total_logs = sum(int(t.get("Occurrences") or 0) for t in templates)
    lines = [
        f"# {dataset} 日志模板",
        "",
        f"> 来源: **loghub-2.0 / {dataset}**  ",
        f"> 模板数: **{len(templates)}**  ",
        f"> 覆盖日志量: **{total_logs:,}** 行  ",
        f"> 用途: 该系统常见日志模式速查; 诊断时按模式匹配定位异常日志。",
        "",
        "每条模板中的 `<*>` 是被参数化的可变字段 (IP / blockId / 数值等)。",
        "",
    ]
    for t in templates:
        eid = (t.get("EventId") or "").strip() or "E?"
        tmpl = (t.get("EventTemplate") or "").strip()
        try:
            occ = int(t.get("Occurrences") or 0)
        except Exception:
            occ = 0
        lines += [
            f"## {eid} (出现 {occ:,} 次)",
            "",
            "```log",
            tmpl or "(empty template)",
            "```",
        ]
        sample = samples.get(eid)
        if sample:
            lines += ["", f"样例: `{sample[:300]}`"]
        lines.append("")
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description="loghub *_templates.csv -> kb_corpus/*.md")
    parser.add_argument("--src", type=str, default=str(SRC_DEFAULT), help="loghub2 根目录")
    parser.add_argument("--no-samples", action="store_true", help="不抓真实日志样例")
    parser.add_argument("--sample-scan-lines", type=int, default=50000, help="抓样例时扫描的行数上限")
    parser.add_argument("--dry-run", action="store_true", help="只统计, 不写文件")
    args = parser.parse_args()

    src = Path(args.src)
    if not src.exists():
        print(f"[error] loghub 源目录不存在: {src}")
        print("       用 --src 指定, 例如 --src '/path/to/loghub2'")
        sys.exit(1)

    if not args.dry_run:
        OUT.mkdir(parents=True, exist_ok=True)
        for f in OUT.glob("*_log_templates.md"):
            f.unlink()

    grand_templates = 0
    written = 0
    for ds in DATASETS:
        tpath = _find_csv(src, ds, "templates.csv")
        if tpath is None:
            print(f"[skip] {ds}: 找不到 templates.csv")
            continue
        templates = load_templates(tpath)
        samples: dict[str, str] = {}
        if not args.no_samples:
            spath = _find_csv(src, ds, "structured.csv")
            samples = collect_samples(spath, args.sample_scan_lines)
        grand_templates += len(templates)

        md = render_dataset(ds, templates, samples)
        if args.dry_run:
            print(f"[dry-run] {ds}: {len(templates)} 模板, {len(samples)} 条样例, "
                  f"md {len(md):,} 字符")
            continue
        out_path = OUT / f"{ds}_log_templates.md"
        out_path.write_text(md, encoding="utf-8")
        written += 1
        print(f"[ok] {ds}: {len(templates)} 模板 ({len(samples)} 样例) -> {out_path.name}")

    print(f"[done] 数据集 {len(DATASETS)}, 模板合计 {grand_templates}, "
          f"{'(dry-run, 未写)' if args.dry_run else f'写出 {written} 个 .md -> {OUT}'}")
    if not args.dry_run:
        print("       下一步: python scripts/ingest_kb_corpus.py  (会自动扫到 log_templates/*.md)")


if __name__ == "__main__":
    main()
