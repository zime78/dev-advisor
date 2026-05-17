#!/usr/bin/env python3
"""Generate and verify dev-advisor catalog-index.json.

The Markdown references remain the source of truth. This script builds a
machine-readable lookup index from the checked-in catalog files and can fail
when the generated JSON is stale.
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


DOMAINS = ("patterns", "algorithms", "languages", "security", "principles", "quality")
ENTRY_COUNT_KEYS = {
    "patterns": "EXPECTED_PATTERNS",
    "algorithms": "EXPECTED_ALGORITHMS",
    "languages": "EXPECTED_LANGUAGES",
    "security": "EXPECTED_SECURITY",
    "principles": "EXPECTED_PRINCIPLES",
    "quality": "EXPECTED_QUALITY",
}


def strip_md(text: str) -> str:
    text = re.sub(r"`([^`]*)`", r"\1", text)
    text = re.sub(r"\[([^\]\n]+)\]\([^)]+\)", r"\1", text)
    text = re.sub(r"<[^>]+>", "", text)
    return text.strip()


def slugify(text: str) -> str:
    text = re.sub(r"<[^>]+>", "", text)
    text = re.sub(r"[`*_~]", "", text).strip().lower()
    text = re.sub(r"[^\w\s\-\u3131-\u318E\uAC00-\uD7A3]+", " ", text)
    text = re.sub(r"\s+", "-", text)
    text = re.sub(r"-+", "-", text)
    return text.strip("-")


def normalize_key(text: str) -> str:
    return slugify(strip_md(text))


def strip_ordinal_prefix(text: str) -> str:
    return re.sub(r"^\d+-", "", text)


def first_heading(path: Path) -> tuple[str, str]:
    for line in path.read_text(encoding="utf-8").splitlines():
        match = re.match(r"^#\s+(.+?)\s*$", line)
        if match:
            title = strip_md(match.group(1))
            return title, slugify(title)
    title = path.stem
    return title, slugify(title)


def read_manifest(skill_dir: Path) -> dict[str, int]:
    candidates = [
        skill_dir.parents[3] / ".counts.manifest",
        skill_dir / ".counts.manifest",
    ]
    for path in candidates:
        if not path.exists():
            continue
        values: dict[str, int] = {}
        for line in path.read_text(encoding="utf-8").splitlines():
            match = re.match(r"^([A-Z0-9_]+)=(\d+)$", line.strip())
            if match:
                values[match.group(1)] = int(match.group(2))
        return values
    raise SystemExit(f"FATAL: .counts.manifest not found for {skill_dir}")


def generated_at() -> str:
    epoch = os.environ.get("SOURCE_DATE_EPOCH")
    if epoch:
        dt = datetime.fromtimestamp(int(epoch), tz=timezone.utc)
    else:
        dt = datetime.now(tz=timezone.utc)
    return dt.replace(microsecond=0).isoformat().replace("+00:00", "Z")


def parse_numbered_title(raw: str) -> tuple[int, str, str | None]:
    match = re.match(r"^##\s+(\d+)\.\s+(.+?)\s*$", raw)
    if not match:
        raise ValueError(raw)
    ordinal = int(match.group(1))
    title = strip_md(match.group(2))
    title_ko = None
    ko_match = re.search(r"\(([^()]*[\u3131-\u318E\uAC00-\uD7A3][^()]*)\)\s*$", title)
    if ko_match:
        title_ko = ko_match.group(1).strip()
        title = title[: ko_match.start()].strip()
    return ordinal, title, title_ko


def collect_anchors(path: Path) -> set[str]:
    text = path.read_text(encoding="utf-8")
    anchors = set(re.findall(r'<a\s+id="([^"]+)"', text))
    for line in text.splitlines():
        match = re.match(r"^#{1,6}\s+(.+?)\s*$", line)
        if not match:
            continue
        slug = slugify(match.group(1))
        if slug:
            anchors.add(slug)
            anchors.add(re.sub(r"^\d+-", "", slug))
    return anchors


def anchor_matches(fragment: str, anchors: set[str]) -> bool:
    return fragment in anchors or any(anchor.startswith(fragment + "-") for anchor in anchors)


def numbered_entries(path: Path) -> list[dict[str, Any]]:
    entries: list[dict[str, Any]] = []
    pending_anchor: str | None = None
    following_anchor_entry: int | None = None
    for line in path.read_text(encoding="utf-8").splitlines():
        if re.match(r"^##\s+\d+\.", line):
            inline_anchor = re.search(r'<a\s+id="([^"]+)"', line)
            ordinal, title, title_ko = parse_numbered_title(line)
            heading_anchor = slugify(line.lstrip("#").strip())
            entries.append(
                {
                    "ordinal": ordinal,
                    "title": title,
                    "title_ko": title_ko,
                    "anchor": (inline_anchor.group(1) if inline_anchor else pending_anchor) or heading_anchor,
                    "heading_anchor": heading_anchor,
                }
            )
            following_anchor_entry = None if inline_anchor or pending_anchor else len(entries) - 1
            pending_anchor = None
            continue
        anchor_match = re.search(r'<a\s+id="([^"]+)"', line)
        if anchor_match:
            if following_anchor_entry is not None:
                entries[following_anchor_entry]["anchor"] = anchor_match.group(1)
                following_anchor_entry = None
            else:
                pending_anchor = anchor_match.group(1)
            continue
        if line.strip() and not line.startswith("<!--"):
            pending_anchor = None
            following_anchor_entry = None
    return entries


def item(
    *,
    domain: str,
    item_id: str,
    title: str,
    title_ko: str | None,
    category: str,
    file_path: str,
    anchor: str,
    aliases: list[str] | None = None,
    tags: list[str] | None = None,
    item_type: str = "entry",
) -> dict[str, Any]:
    alias_list = sorted(set(aliases or []))
    tag_list = sorted(set(tags or []))
    keys = [item_id, title]
    if title_ko:
        keys.append(title_ko)
    keys.extend(alias_list)
    return {
        "domain": domain,
        "id": item_id,
        "item_type": item_type,
        "title": title,
        "title_ko": title_ko,
        "category": category,
        "file": file_path,
        "anchor": anchor,
        "aliases": alias_list,
        "tags": tag_list,
        "lookup_keys": sorted({key for key in (normalize_key(k) for k in keys) if key}),
    }


def parse_alias_table(index_path: Path, heading_re: str) -> list[dict[str, str]]:
    aliases: list[dict[str, str]] = []
    in_alias = False
    for line in index_path.read_text(encoding="utf-8").splitlines():
        if re.match(heading_re, line):
            in_alias = True
            continue
        if in_alias and line.startswith("## "):
            break
        if not in_alias:
            continue
        row = re.match(r"^\|\s*`?([^`|]+?)`?\s*\|\s*`?([^`|]+?)`?\s*(?:\||$)", line)
        if not row:
            continue
        alias = strip_md(row.group(1))
        primary = strip_md(row.group(2))
        if alias in {"별칭", "Alias"} or primary == "Primary ID" or set(alias) <= set("-: "):
            continue
        aliases.append({"alias": alias, "target_id": primary, "source": str(index_path.name)})
    return aliases


def parse_simple_mapping(index_path: Path, start_re: str, stop_re: str) -> dict[tuple[str, int], dict[str, str]]:
    rows: dict[tuple[str, int], dict[str, str]] = {}
    current_file: str | None = None
    ordinal = 0
    in_mapping = False
    in_table = False
    for line in index_path.read_text(encoding="utf-8").splitlines():
        if re.match(start_re, line):
            in_mapping = True
            continue
        if in_mapping and re.match(stop_re, line):
            break
        if not in_mapping:
            continue
        section = re.match(r"^### .+?\(([A-Za-z0-9_./-]+\.md)(?:,[^)]*)?\).*$", line)
        if section:
            current_file = section.group(1)
            ordinal = 0
            in_table = False
            continue
        if re.match(r"^\|\s*ID\s*\|\s*영문명\s*\|", line):
            in_table = True
            continue
        if in_table and re.match(r"^\|[-: ]+\|", line):
            continue
        if in_table and not line.startswith("|"):
            in_table = False
            continue
        if not (current_file and in_table):
            continue
        row = re.match(r"^\|\s*`?([^`|]+?)`?\s*\|\s*(.*?)\s*\|\s*(.*?)\s*\|", line)
        if not row:
            continue
        ordinal += 1
        rows[(current_file, ordinal)] = {
            "id": strip_md(row.group(1)),
            "title": strip_md(row.group(2)),
            "title_ko": strip_md(row.group(3)),
        }
    return rows


def generate_from_numbered_files(
    refs: Path,
    domain: str,
    mapping: dict[tuple[str, int], dict[str, str]] | None = None,
    *,
    exclude: set[str] | None = None,
) -> list[dict[str, Any]]:
    mapping = mapping or {}
    exclude = exclude or set()
    items: list[dict[str, Any]] = []
    for path in sorted((refs / domain).rglob("*.md")):
        rel_file = path.relative_to(refs / domain).as_posix()
        if path.name == "index.md" or rel_file in exclude:
            continue
        category = path.with_suffix("").relative_to(refs / domain).as_posix()
        for entry in numbered_entries(path):
            meta = mapping.get((rel_file, entry["ordinal"]), {})
            item_id = meta.get("id") or entry["anchor"] or re.sub(r"^\d+-", "", entry["heading_anchor"])
            title = meta.get("title") or entry["title"]
            title_ko = meta.get("title_ko") or entry["title_ko"]
            items.append(
                item(
                    domain=domain,
                    item_id=item_id,
                    title=title,
                    title_ko=title_ko,
                    category=category,
                    file_path=f"references/{domain}/{rel_file}",
                    anchor=entry["anchor"],
                )
            )
    return items


def generate_patterns(refs: Path) -> list[dict[str, Any]]:
    mapping = parse_simple_mapping(
        refs / "patterns" / "index.md",
        r"^## 패턴 ID",
        r"^## 패턴 선택",
    )
    return generate_from_numbered_files(refs, "patterns", mapping)


def generate_security(refs: Path) -> list[dict[str, Any]]:
    mapping = parse_simple_mapping(
        refs / "security" / "index.md",
        r"^## 보안 ID",
        r"^## 표준 인용",
    )
    items: list[dict[str, Any]] = []
    for (rel_file, ordinal), meta in sorted(mapping.items()):
        path = refs / "security" / rel_file
        entries = {entry["ordinal"]: entry for entry in numbered_entries(path)}
        entry = entries.get(ordinal)
        if not entry:
            entry = {"anchor": meta["id"], "title": meta["title"], "title_ko": meta.get("title_ko")}
        items.append(
            item(
                domain="security",
                item_id=meta["id"],
                title=meta["title"],
                title_ko=meta.get("title_ko"),
                category=Path(rel_file).with_suffix("").as_posix(),
                file_path=f"references/security/{rel_file}",
                anchor=entry["anchor"],
            )
        )
    return items


def generate_algorithms(refs: Path) -> list[dict[str, Any]]:
    index_path = refs / "algorithms" / "index.md"
    items: list[dict[str, Any]] = []
    in_mapping = False
    for line in index_path.read_text(encoding="utf-8").splitlines():
        if re.match(r"^## 알고리즘 ID 매핑", line):
            in_mapping = True
            continue
        if in_mapping and re.match(r"^## ", line):
            break
        if not in_mapping:
            continue
        row = re.match(
            r"^\|\s*`?([^`|]+?)`?\s*\|\s*(.*?)\s*\|\s*(.*?)\s*\|\s*(.*?)\s*\|\s*\[[^\]]+\]\(([^)#]+\.md)#([^)]*)\)",
            line,
        )
        if not row:
            continue
        item_id, title, title_ko, category, file_name, anchor = [strip_md(part) for part in row.groups()]
        items.append(
            item(
                domain="algorithms",
                item_id=item_id,
                title=title,
                title_ko=title_ko,
                category=category,
                file_path=f"references/algorithms/{file_name}",
                anchor=anchor,
            )
        )
    return items


def generate_languages(refs: Path) -> list[dict[str, Any]]:
    lang_dir = refs / "languages"
    items: list[dict[str, Any]] = []
    for path in sorted(lang_dir.glob("*.md")):
        if path.name in {"index.md", "domains.md"}:
            continue
        lang_id = path.stem
        title = lang_id
        for line in path.read_text(encoding="utf-8").splitlines():
            if line.startswith("# "):
                title = strip_md(line[2:])
                break
        items.append(
            item(
                domain="languages",
                item_id=lang_id,
                title=title,
                title_ko=None,
                category="language",
                file_path=f"references/languages/{path.name}",
                anchor=slugify(title) or lang_id,
            )
        )
    return items


PRINCIPLE_PREFIXES = {
    "12-factor.md": "12f",
    "code-smells.md": "code-smell",
    "concurrency-theory.md": "conc",
    "documentation.md": "doc",
    "evolutionary-arch.md": "evo",
    "iso25010.md": "iso",
    "performance-metrics.md": "perf",
    "process-metrics.md": "proc",
    "refactoring-techniques.md": "refactor",
    "resilience-theory.md": "res",
    "sustainable-sw.md": "green",
    "sw-economics.md": "econ",
    "type-systems.md": "type",
}

PRINCIPLE_ID_OVERRIDES = {
    ("solid.md", 1): "srp",
    ("solid.md", 2): "ocp",
    ("solid.md", 3): "lsp",
    ("solid.md", 4): "isp",
    ("solid.md", 5): "dip",
    ("grasp.md", 1): "information-expert",
    ("grasp.md", 2): "creator",
    ("grasp.md", 3): "controller",
    ("grasp.md", 4): "low-coupling",
    ("grasp.md", 5): "high-cohesion",
    ("grasp.md", 6): "polymorphism",
    ("grasp.md", 7): "pure-fabrication",
    ("grasp.md", 8): "indirection",
    ("grasp.md", 9): "protected-variations",
    ("iso25010.md", 1): "iso-functional-suitability",
    ("iso25010.md", 2): "iso-performance-efficiency",
    ("iso25010.md", 3): "iso-compatibility",
    ("iso25010.md", 4): "iso-usability",
    ("iso25010.md", 5): "iso-reliability",
    ("iso25010.md", 6): "iso-security",
    ("iso25010.md", 7): "iso-maintainability",
    ("iso25010.md", 8): "iso-portability",
    ("type-systems.md", 1): "type-static-vs-dynamic",
    ("type-systems.md", 2): "type-strong-vs-weak",
    ("type-systems.md", 3): "type-nominal-vs-structural",
    ("concurrency-theory.md", 3): "conc-sequential-consistency",
    ("concurrency-theory.md", 4): "conc-causal-consistency",
    ("concurrency-theory.md", 5): "conc-eventual-consistency",
    ("concurrency-theory.md", 6): "conc-snapshot-isolation",
    ("concurrency-theory.md", 8): "conc-liveness-safety",
    ("concurrency-theory.md", 9): "conc-deadlock",
    ("concurrency-theory.md", 10): "conc-race-condition",
    ("resilience-theory.md", 3): "res-safety-i-ii",
    ("resilience-theory.md", 7): "res-chaos-engineering",
    ("sw-economics.md", 2): "econ-cocomo",
    ("sw-economics.md", 8): "econ-cod",
    ("sw-economics.md", 10): "econ-rcf",
    ("process-metrics.md", 4): "proc-dora",
    ("process-metrics.md", 5): "proc-space",
    ("process-metrics.md", 6): "proc-trunk-based",
    ("process-metrics.md", 8): "proc-platform-engineering",
    ("performance-metrics.md", 1): "perf-dean-numbers",
    ("performance-metrics.md", 5): "perf-halstead",
    ("performance-metrics.md", 7): "perf-flame-graph",
    ("performance-metrics.md", 8): "perf-tail-latency",
    ("performance-metrics.md", 10): "perf-apdex",
    ("sustainable-sw.md", 1): "green-carbon-aware",
    ("sustainable-sw.md", 4): "green-sci",
    ("sustainable-sw.md", 8): "green-efficient-data",
}

MICRO_PRINCIPLE_ID_OVERRIDES = {
    "conway-law": "conway",
    "hyrum-law": "hyrum",
    "postel-law": "postel",
    "brooks-law": "brooks",
    "hollywood-principle": "hollywood",
    "boy-scout-rule": "boy-scout",
    "pareto-principle": "pareto",
    "goodhart-law": "goodhart",
    "cunningham-law": "cunningham",
}


def principle_entry_id(rel_file: str, entry: dict[str, Any]) -> str:
    override = PRINCIPLE_ID_OVERRIDES.get((rel_file, entry["ordinal"]))
    if override:
        return override

    base = strip_ordinal_prefix(entry["anchor"] or entry["heading_anchor"])
    prefix = PRINCIPLE_PREFIXES.get(rel_file)
    if prefix and not base.startswith(prefix + "-"):
        return f"{prefix}-{base}"
    return base


def parse_principles_categories(index_path: Path, refs: Path) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    in_domain = False
    for line in index_path.read_text(encoding="utf-8").splitlines():
        if re.match(r"^## 도메인 진입점", line):
            in_domain = True
            continue
        if in_domain and re.match(r"^## 카테고리 선택 가이드", line):
            break
        if not in_domain:
            continue
        row = re.match(r"^\|\s*\d+\s*\|\s*\[([^\]]+\.md)\]\(([^)#]+\.md)\)\s*\|", line)
        if not row:
            continue
        label, file_name = row.groups()
        path = refs / "principles" / file_name
        title, anchor = first_heading(path)
        items.append(
            item(
                domain="principles",
                item_id=Path(file_name).stem,
                title=title,
                title_ko=None,
                category="category",
                file_path=f"references/principles/{file_name}",
                anchor=anchor or Path(file_name).stem,
                aliases=[] if label == file_name else [Path(label).stem],
                item_type="category",
            )
        )
    return items


def generate_micro_principles(refs: Path) -> list[dict[str, Any]]:
    path = refs / "principles" / "micro-principles.md"
    items: list[dict[str, Any]] = []
    pending_anchor: str | None = None
    for line in path.read_text(encoding="utf-8").splitlines():
        anchor_match = re.search(r'<a\s+id="([^"]+)"', line)
        if anchor_match:
            pending_anchor = anchor_match.group(1)
            continue
        if not pending_anchor:
            continue
        heading_match = re.match(r"^##\s+(.+?)\s*$", line)
        if not heading_match:
            continue
        title = strip_md(heading_match.group(1))
        items.append(
            item(
                domain="principles",
                item_id=MICRO_PRINCIPLE_ID_OVERRIDES.get(pending_anchor, pending_anchor),
                title=title,
                title_ko=None,
                category="micro-principles",
                file_path="references/principles/micro-principles.md",
                anchor=pending_anchor,
                item_type="appendix",
            )
        )
        pending_anchor = None
    return items


def generate_principles(refs: Path) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    for path in sorted((refs / "principles").glob("*.md")):
        rel_file = path.name
        if rel_file in {"index.md", "micro-principles.md"}:
            continue
        category = path.stem
        for entry in numbered_entries(path):
            items.append(
                item(
                    domain="principles",
                    item_id=principle_entry_id(rel_file, entry),
                    title=entry["title"],
                    title_ko=entry["title_ko"],
                    category=category,
                    file_path=f"references/principles/{rel_file}",
                    anchor=entry["anchor"],
                )
            )
    items.extend(parse_principles_categories(refs / "principles" / "index.md", refs))
    items.extend(generate_micro_principles(refs))
    return items


def item_type_counts(items: list[dict[str, Any]], domain: str) -> dict[str, int]:
    counts: dict[str, int] = {}
    for entry in items:
        if entry["domain"] != domain:
            continue
        item_type = entry.get("item_type", "entry")
        counts[item_type] = counts.get(item_type, 0) + 1
    return dict(sorted(counts.items()))


def generate_quality(refs: Path) -> list[dict[str, Any]]:
    index_path = refs / "quality" / "index.md"
    items: list[dict[str, Any]] = []
    in_mapping = False
    for line in index_path.read_text(encoding="utf-8").splitlines():
        if re.match(r"^## Quality ID 매핑", line):
            in_mapping = True
            continue
        if in_mapping and re.match(r"^## ", line):
            break
        if not in_mapping:
            continue
        row = re.match(
            r"^\|\s*`([^`]+)`\s*\|\s*\[[^\]]+\]\(([^)#]+\.md)#([^)]*)\)\s*\|\s*(.*?)\s*\|\s*(.*?)\s*\|",
            line,
        )
        if not row:
            continue
        item_id, file_name, anchor, title, tags = [strip_md(part) for part in row.groups()]
        items.append(
            item(
                domain="quality",
                item_id=item_id,
                title=title,
                title_ko=None,
                category=Path(file_name).stem,
                file_path=f"references/quality/{file_name}",
                anchor=anchor,
                tags=[tag.strip() for tag in tags.split(",") if tag.strip()],
            )
        )
    return items


def collect_aliases(refs: Path, items: list[dict[str, Any]]) -> list[dict[str, str]]:
    ids_by_domain: dict[str, set[str]] = {}
    aliases_by_target: dict[tuple[str, str], list[str]] = {}
    for entry in items:
        ids_by_domain.setdefault(entry["domain"], set()).add(entry["id"])

    specs = [
        ("algorithms", refs / "algorithms" / "index.md", r"^### 알고리즘 별칭"),
        ("languages", refs / "languages" / "index.md", r"^### 언어 별칭"),
        ("principles", refs / "principles" / "index.md", r"^### 별칭"),
        ("quality", refs / "quality" / "index.md", r"^## 별칭"),
    ]
    aliases: list[dict[str, str]] = []
    for domain, index_path, heading_re in specs:
        for parsed in parse_alias_table(index_path, heading_re):
            alias = parsed["alias"]
            target_id = parsed["target_id"]
            aliases.append(
                {
                    "domain": domain,
                    "alias": alias,
                    "target_id": target_id,
                    "source": f"references/{domain}/index.md",
                }
            )
            if target_id in ids_by_domain.get(domain, set()):
                aliases_by_target.setdefault((domain, target_id), []).append(alias)

    for entry in items:
        entry["aliases"] = sorted(aliases_by_target.get((entry["domain"], entry["id"]), []))
        keys = [entry["id"], entry["title"], *entry["aliases"]]
        if entry.get("title_ko"):
            keys.append(entry["title_ko"])
        entry["lookup_keys"] = sorted({key for key in (normalize_key(k) for k in keys) if key})

    return sorted(aliases, key=lambda row: (row["domain"], row["alias"]))


def validate(skill_dir: Path, catalog: dict[str, Any], manifest: dict[str, int]) -> list[str]:
    issues: list[str] = []
    refs = skill_dir / "references"
    ids: dict[tuple[str, str], str] = {}
    anchors_cache: dict[Path, set[str]] = {}
    entry_counts = {domain: 0 for domain in DOMAINS}

    for entry in catalog["items"]:
        key = (entry["domain"], entry["id"])
        if key in ids:
            issues.append(f"duplicate item id: {entry['domain']}/{entry['id']}")
        ids[key] = entry["file"]
        if entry.get("item_type", "entry") == "entry":
            entry_counts[entry["domain"]] += 1
        path = skill_dir / entry["file"]
        if not path.exists():
            issues.append(f"missing file: {entry['file']}")
            continue
        if path not in anchors_cache:
            anchors_cache[path] = collect_anchors(path)
        if not anchor_matches(entry["anchor"], anchors_cache[path]):
            issues.append(f"missing anchor: {entry['file']}#{entry['anchor']}")

    for domain, manifest_key in ENTRY_COUNT_KEYS.items():
        expected = manifest.get(manifest_key)
        if expected is not None and entry_counts[domain] != expected:
            issues.append(f"{domain} entry count mismatch: expected={expected}, actual={entry_counts[domain]}")

    alias_keys: dict[tuple[str, str], str] = {}
    for row in catalog["aliases"]:
        key = (row["domain"], row["alias"].strip().lower())
        if key in alias_keys:
            issues.append(f"duplicate alias: {row['domain']}/{row['alias']}")
        alias_keys[key] = row["target_id"]
        if (row["domain"], row["target_id"]) not in ids:
            issues.append(f"alias target missing: {row['domain']}/{row['alias']} -> {row['target_id']}")

    for domain, summary in catalog["domains"].items():
        if summary["actual_count"] != entry_counts[domain]:
            issues.append(
                f"domain summary mismatch: {domain} actual_count={summary['actual_count']} entries={entry_counts[domain]}"
            )
    return issues


def build_catalog(skill_dir: Path) -> dict[str, Any]:
    refs = skill_dir / "references"
    manifest = read_manifest(skill_dir)
    items: list[dict[str, Any]] = []
    items.extend(generate_patterns(refs))
    items.extend(generate_algorithms(refs))
    items.extend(generate_languages(refs))
    items.extend(generate_security(refs))
    items.extend(generate_principles(refs))
    items.extend(generate_quality(refs))
    items.sort(key=lambda row: (row["domain"], row["category"], row["id"]))
    aliases = collect_aliases(refs, items)

    counts = {domain: 0 for domain in DOMAINS}
    for entry in items:
        if entry.get("item_type", "entry") == "entry":
            counts[entry["domain"]] += 1

    domains = {
        domain: {
            "index": f"references/{domain}/index.md",
            "expected_count": manifest[ENTRY_COUNT_KEYS[domain]],
            "actual_count": counts[domain],
            "lookup_count": sum(1 for entry in items if entry["domain"] == domain),
            "item_type_counts": item_type_counts(items, domain),
        }
        for domain in DOMAINS
    }

    catalog = {
        "schema_version": "1.0",
        "catalog_version": "2026-05",
        "generated_at": generated_at(),
        "source": {
            "root": "references",
            "generator": "scripts/generate-catalog-index.py",
            "source_of_truth": "markdown",
        },
        "domains": domains,
        "items": items,
        "aliases": aliases,
    }

    issues = validate(skill_dir, catalog, manifest)
    if issues:
        for issue in issues[:100]:
            print(f"FATAL: {issue}", file=sys.stderr)
        if len(issues) > 100:
            print(f"FATAL: ... {len(issues) - 100} more", file=sys.stderr)
        raise SystemExit(1)
    return catalog


def normalize_for_check(catalog: dict[str, Any]) -> dict[str, Any]:
    normalized = copy.deepcopy(catalog)
    normalized["generated_at"] = "<ignored>"
    return normalized


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate dev-advisor catalog-index.json")
    parser.add_argument("--check", action="store_true", help="fail when catalog-index.json is stale")
    parser.add_argument("--output", default="catalog-index.json", help="output path relative to skill root")
    parser.add_argument("--pretty", action="store_true", default=True, help="write pretty deterministic JSON")
    args = parser.parse_args()

    script_dir = Path(__file__).resolve().parent
    skill_dir = script_dir.parent
    output = Path(args.output)
    if not output.is_absolute():
        output = skill_dir / output

    catalog = build_catalog(skill_dir)
    text = json.dumps(catalog, ensure_ascii=False, indent=2, sort_keys=False) + "\n"

    if args.check:
        if not output.exists():
            print(f"FATAL: missing {output}", file=sys.stderr)
            return 1
        existing = json.loads(output.read_text(encoding="utf-8"))
        if normalize_for_check(existing) != normalize_for_check(catalog):
            print(f"FATAL: stale {output}", file=sys.stderr)
            return 1
        print(
            "catalog-index.json OK "
            f"({len(catalog['items'])} items, {len(catalog['aliases'])} aliases)"
        )
        return 0

    output.write_text(text, encoding="utf-8")
    print(f"wrote {output} ({len(catalog['items'])} items, {len(catalog['aliases'])} aliases)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
