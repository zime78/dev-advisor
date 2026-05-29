#!/usr/bin/env python3
"""Generate and verify dev-advisor catalog-index.json.

The Markdown references remain the source of truth. This script builds a
machine-readable lookup index from the checked-in catalog files and can fail
when the generated JSON is stale.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import os
import pickle
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
    text = strip_md(text).lower()
    symbol_aliases = {
        "c++": "cplusplus",
        "c#": "csharp",
        "f#": "fsharp",
        "vb.net": "vb dotnet",
    }
    for source, target in symbol_aliases.items():
        text = text.replace(source, target)
    return slugify(text)


def strip_ordinal_prefix(text: str) -> str:
    return re.sub(r"^\d+-", "", text)


def build_lookup_keys(keys: list[str]) -> list[str]:
    lookup_keys = {key for key in (normalize_key(k) for k in keys) if key}
    lookup_keys.update(
        key.replace("-c-cplusplus", "-cplusplus")
        for key in list(lookup_keys)
        if "-c-cplusplus" in key
    )
    return sorted(lookup_keys)


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
        "lookup_keys": build_lookup_keys(keys),
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


def split_md_table_row(line: str) -> list[str]:
    if not line.startswith("|"):
        return []
    return [cell.strip() for cell in line.strip().strip("|").split("|")]


STANDARD_SECTION_RE = re.compile(r"^(?:##|###)\s+(.+?)\s*$")

STANDARD_IDS = {
    "swebok v4": "swebok-v4",
    "computing curricula 2023": "cs2023",
    "cs2023": "cs2023",
    "dama-dmbok 2": "dmbok-2",
    "dmbok 2": "dmbok-2",
    "owasp web top 10": "owasp-web-2021",
    "owasp api security top 10": "owasp-api-2023",
    "owasp mobile top 10": "owasp-mobile-2024",
    "owasp llm top 10": "owasp-llm-2025",
    "nist 800-series": "nist-800-series",
    "iso/iec 정보보안 표준": "iso-iec-security",
    "iso/iec 25010:2023 8 특성": "iso-iec-25010",
    "iso/iec 25010": "iso-iec-25010",
    "dora 4 key metrics": "dora",
}

STANDARD_ALIASES = {
    "swebok-v4": ["SWEBOK", "SWEBOK V4"],
    "cs2023": ["CS2023", "Computing Curricula 2023"],
    "dmbok-2": ["DMBOK", "DMBOK 2", "DAMA DMBOK"],
    "owasp-web-2021": ["OWASP", "OWASP Web", "OWASP Web 2021"],
    "owasp-api-2023": ["OWASP", "OWASP API", "OWASP API 2023"],
    "owasp-mobile-2024": ["OWASP", "OWASP Mobile", "OWASP Mobile 2024"],
    "owasp-llm-2025": ["OWASP", "OWASP LLM", "OWASP LLM 2025"],
    "nist-800-series": ["NIST", "NIST 800", "NIST 800-series"],
    "iso-iec-security": ["ISO", "ISO IEC", "ISO/IEC security"],
    "iso-iec-25010": ["ISO 25010", "ISO/IEC 25010", "ISO 25010:2023", "ISO/IEC 25010:2023", "Product Quality Model"],
    "dora": ["DORA", "DORA Metrics", "DORA Four Keys", "DORA 4 Key Metrics"],
}


def standard_from_heading(heading: str) -> str | None:
    normalized = normalize_key(strip_ordinal_prefix(slugify(heading)).replace("-", " "))
    heading_lower = strip_md(heading).lower()
    for needle, standard_id in STANDARD_IDS.items():
        if needle in heading_lower:
            return standard_id
    if "owasp" in heading_lower and "web" in heading_lower:
        return "owasp-web-2021"
    if "owasp" in heading_lower and "api" in heading_lower:
        return "owasp-api-2023"
    if "owasp" in heading_lower and "mobile" in heading_lower:
        return "owasp-mobile-2024"
    if "owasp" in heading_lower and "llm" in heading_lower:
        return "owasp-llm-2025"
    if "nist" in heading_lower and "800" in heading_lower:
        return "nist-800-series"
    if "iso/iec" in heading_lower and "표준" in heading_lower:
        return "iso-iec-security"
    if normalized in STANDARD_IDS:
        return STANDARD_IDS[normalized]
    return None


def clean_standard_cell(text: str) -> str:
    text = strip_md(text)
    text = re.sub(r"[*_~]+", "", text)
    return text.strip()


def ordinal_references(refs: Path, rel_file: str, suffix: str) -> list[str]:
    ordinals = [int(match) for match in re.findall(r"§\s*(\d+)", suffix)]
    if not ordinals:
        return []
    path = refs / rel_file
    if not path.exists():
        return []
    entries = {entry["ordinal"]: entry for entry in numbered_entries(path)}
    return [
        f"references/{rel_file}#{entries[ordinal]['anchor']}"
        for ordinal in ordinals
        if ordinal in entries
    ]


def extract_backtick_refs(cell: str, refs: Path) -> list[str]:
    references: list[str] = []
    current_file: str | None = None
    matches = list(re.finditer(r"`([^`]+)`", cell))
    for index, match in enumerate(matches):
        raw = match.group(1)
        value = raw.strip()
        file_match = re.match(
            r"^((?:patterns|algorithms|languages|security|principles|quality)/[^#\s,)]+\.md)(?:#([^)\s,]+))?$",
            value,
        )
        if file_match:
            current_file = file_match.group(1)
            fragment = file_match.group(2)
            if fragment:
                references.append(f"references/{current_file}#{fragment}")
            else:
                next_start = matches[index + 1].start() if index + 1 < len(matches) else len(cell)
                suffix = cell[match.end() : next_start]
                ordinal_refs = ordinal_references(refs, current_file, suffix)
                references.extend(ordinal_refs or [f"references/{current_file}"])
            continue
        fragment_match = re.match(r"^#([^)\s,]+)$", value)
        if fragment_match and current_file:
            references.append(f"references/{current_file}#{fragment_match.group(1)}")
    if not references and "SWEBOK" in cell and "§1" in cell:
        references.append("references/principles/standards-mapping.md#swebok-v4-mapping")
    return references


def parse_code_title(standard: str, headers: list[str], cells: list[str]) -> tuple[str, str]:
    cleaned = [clean_standard_cell(cell) for cell in cells]
    if standard.startswith("owasp-"):
        return cleaned[0], cleaned[1]
    if standard in {"nist-800-series", "iso-iec-security"}:
        return cleaned[0], cleaned[1]
    if standard == "cs2023":
        match = re.match(r"^([A-Z]+)\s*[—-]\s*(.+)$", cleaned[1])
        if match:
            return match.group(1), match.group(2)
        return cleaned[0], cleaned[1]
    if standard == "dmbok-2":
        return cleaned[0], cleaned[1]
    if standard == "swebok-v4":
        return cleaned[0], cleaned[1]
    code_index = 0
    title_index = 1 if len(cleaned) > 1 else 0
    return cleaned[code_index], cleaned[title_index]


def standard_lookup_keys(standard: str, code: str, title: str, coverage: str) -> list[str]:
    raw_keys = [standard, code, title, coverage, f"{standard} {code}", f"{standard} {title}"]
    if code.isdigit():
        raw_keys.extend([f"KA{code}", f"KA {code}", f"{standard} KA{code}", f"{standard} KA {code}"])
    code_match = re.match(r"^([A-Za-z]+)(\d+)$", code)
    spaced_code = f"{code_match.group(1)} {code_match.group(2)}" if code_match else None
    if spaced_code:
        raw_keys.extend([spaced_code, f"{standard} {spaced_code}"])
    for alias in STANDARD_ALIASES.get(standard, []):
        raw_keys.extend([alias, f"{alias} {code}", f"{alias}{code}", f"{alias} {title}"])
        if code.isdigit():
            raw_keys.extend([f"{alias} KA{code}", f"{alias} KA {code}"])
        if spaced_code:
            raw_keys.extend([f"{alias} {spaced_code}", f"{alias}{spaced_code}"])
    return sorted({key for key in (normalize_key(raw) for raw in raw_keys) if key})


def generate_standards_mappings(refs: Path) -> list[dict[str, Any]]:
    path = refs / "principles" / "standards-mapping.md"
    mappings: list[dict[str, Any]] = []
    current_standard: str | None = None
    current_section_id: str | None = None
    headers: list[str] | None = None

    for line in path.read_text(encoding="utf-8").splitlines():
        heading_match = STANDARD_SECTION_RE.match(line)
        if heading_match:
            standard = standard_from_heading(heading_match.group(1))
            if standard:
                current_standard = standard
                current_section_id = slugify(heading_match.group(1))
            headers = None
            continue

        cells = split_md_table_row(line)
        if not cells:
            continue
        if all(set(cell) <= set("-: ") for cell in cells):
            continue
        if any("커버리지" == strip_md(cell) for cell in cells):
            headers = [strip_md(cell) for cell in cells]
            continue
        if not (current_standard and current_section_id and headers):
            continue
        if len(cells) < len(headers):
            continue

        coverage_index = next((idx for idx, header in enumerate(headers) if header == "커버리지"), len(headers) - 1)
        mapping_index = next(
            (
                idx
                for idx, header in enumerate(headers)
                if "매핑" in header or "dev-advisor" in header
            ),
            None,
        )
        if mapping_index is None:
            continue

        code, title = parse_code_title(current_standard, headers, cells)
        coverage = clean_standard_cell(cells[coverage_index])
        references = sorted(set(extract_backtick_refs(cells[mapping_index], refs)))
        mappings.append(
            {
                "standard": current_standard,
                "section_id": current_section_id,
                "code": code,
                "title": title,
                "coverage": coverage,
                "references": references,
                "lookup_keys": standard_lookup_keys(current_standard, code, title, coverage),
            }
        )

    return sorted(mappings, key=lambda row: (row["standard"], row["code"]))


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
        entry["lookup_keys"] = build_lookup_keys(keys)

    return sorted(aliases, key=lambda row: (row["domain"], row["alias"]))


def annotate_anchors(skill_dir: Path, catalog: dict[str, Any]) -> tuple[int, int]:
    """Validate anchor against target markdown for every catalog item.

    각 item에 anchor_exists: bool / anchor_warning: str|None 필드를 추가한다.
    Returns (valid_count, broken_count).
    """
    anchors_cache: dict[Path, set[str]] = {}
    valid = 0
    broken = 0
    for entry in catalog["items"]:
        path = skill_dir / entry["file"]
        if not path.exists():
            entry["anchor_exists"] = False
            entry["anchor_warning"] = f"missing file: {entry['file']}"
            broken += 1
            continue
        if path not in anchors_cache:
            anchors_cache[path] = collect_anchors(path)
        if anchor_matches(entry["anchor"], anchors_cache[path]):
            entry["anchor_exists"] = True
            entry["anchor_warning"] = None
            valid += 1
        else:
            entry["anchor_exists"] = False
            entry["anchor_warning"] = f"missing anchor: {entry['anchor']}"
            broken += 1
    return valid, broken


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

    standard_keys: dict[tuple[str, str], str] = {}
    for row in catalog.get("standards_mappings", []):
        key = (row["standard"], row["code"])
        if key in standard_keys:
            issues.append(f"duplicate standards mapping: {row['standard']}/{row['code']}")
        standard_keys[key] = row["title"]
        if not row.get("references"):
            issues.append(f"empty standards references: {row['standard']}/{row['code']}")
        for reference in row.get("references", []):
            ref_match = re.match(r"^(references/[^#]+\.md)(?:#(.+))?$", reference)
            if not ref_match:
                issues.append(f"invalid standards reference: {row['standard']}/{row['code']} -> {reference}")
                continue
            ref_file, fragment = ref_match.groups()
            path = skill_dir / ref_file
            if not path.exists():
                issues.append(f"missing standards reference file: {row['standard']}/{row['code']} -> {reference}")
                continue
            if fragment:
                if path not in anchors_cache:
                    anchors_cache[path] = collect_anchors(path)
                if not anchor_matches(fragment, anchors_cache[path]):
                    issues.append(f"missing standards reference anchor: {row['standard']}/{row['code']} -> {reference}")

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
    standards_mappings = generate_standards_mappings(refs)

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
        "schema_version": "1.1",
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
        "standards_mappings": standards_mappings,
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


# ---------------------------------------------------------------------------
# State directory emitters (P2-d: sharding + indexes + pickle + source hashes)
# ---------------------------------------------------------------------------


def _ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def _write_json(path: Path, data: Any) -> None:
    _ensure_dir(path.parent)
    text = json.dumps(data, ensure_ascii=False, indent=2, sort_keys=False) + "\n"
    path.write_text(text, encoding="utf-8")


def split_by_domain(catalog: dict[str, Any]) -> dict[str, list[dict[str, Any]]]:
    """Group items by domain (도메인별 item 그룹화)."""
    by_domain: dict[str, list[dict[str, Any]]] = {domain: [] for domain in DOMAINS}
    for entry in catalog["items"]:
        by_domain.setdefault(entry["domain"], []).append(entry)
    return by_domain


def emit_domain_shards(catalog: dict[str, Any], out_dir: Path) -> dict[str, int]:
    """각 도메인의 items만 모아 별도 JSON으로 분할 저장. Returns {domain: count}."""
    domains_dir = out_dir / "catalog" / "domains"
    _ensure_dir(domains_dir)
    by_domain = split_by_domain(catalog)
    counts: dict[str, int] = {}
    for domain, items in by_domain.items():
        shard_path = domains_dir / f"{domain}.json"
        _write_json(
            shard_path,
            {
                "domain": domain,
                "schema_version": catalog.get("schema_version"),
                "catalog_version": catalog.get("catalog_version"),
                "generated_at": catalog.get("generated_at"),
                "count": len(items),
                "items": items,
            },
        )
        counts[domain] = len(items)
    return counts


def emit_meta(catalog: dict[str, Any], out_dir: Path, shard_counts: dict[str, int]) -> None:
    """meta.json — schema/version/timestamp + per-domain count summary."""
    meta_path = out_dir / "catalog" / "meta.json"
    meta = {
        "schema_version": catalog.get("schema_version"),
        "catalog_version": catalog.get("catalog_version"),
        "generated_at": catalog.get("generated_at"),
        "source": catalog.get("source"),
        "domains": catalog.get("domains"),
        "shard_counts": shard_counts,
        "totals": {
            "items": len(catalog["items"]),
            "aliases": len(catalog.get("aliases", [])),
            "standards_mappings": len(catalog.get("standards_mappings", [])),
        },
    }
    _write_json(meta_path, meta)


def emit_aliases(catalog: dict[str, Any], out_dir: Path) -> None:
    """aliases.json — flat alias table (전체 도메인)."""
    _write_json(out_dir / "catalog" / "aliases.json", {"aliases": catalog.get("aliases", [])})


def emit_standards(catalog: dict[str, Any], out_dir: Path) -> None:
    """standards.json — standards_mappings copy."""
    _write_json(
        out_dir / "catalog" / "standards.json",
        {"standards_mappings": catalog.get("standards_mappings", [])},
    )


def build_by_id_index(catalog: dict[str, Any]) -> dict[str, dict[str, int]]:
    """domain → id → entry_idx (도메인 내 item 리스트의 인덱스)."""
    by_id: dict[str, dict[str, int]] = {domain: {} for domain in DOMAINS}
    domain_idx: dict[str, int] = {domain: 0 for domain in DOMAINS}
    for entry in catalog["items"]:
        domain = entry["domain"]
        by_id.setdefault(domain, {})
        domain_idx.setdefault(domain, 0)
        by_id[domain][entry["id"]] = domain_idx[domain]
        domain_idx[domain] += 1
    return by_id


def build_by_alias_index(catalog: dict[str, Any]) -> dict[str, dict[str, str]]:
    """domain → alias(normalized & lower) → target_id."""
    by_alias: dict[str, dict[str, str]] = {domain: {} for domain in DOMAINS}
    for row in catalog.get("aliases", []):
        domain = row["domain"]
        target_id = row["target_id"]
        by_alias.setdefault(domain, {})
        alias_normalized = normalize_key(row["alias"])
        alias_lower = row["alias"].strip().lower()
        if alias_normalized:
            by_alias[domain][alias_normalized] = target_id
        if alias_lower:
            by_alias[domain][alias_lower] = target_id
    return by_alias


def build_by_lookup_key_index(catalog: dict[str, Any]) -> dict[str, dict[str, list[str]]]:
    """domain → lookup_key → [ids] (검색 시 사전 정규화된 inverted index)."""
    by_key: dict[str, dict[str, list[str]]] = {domain: {} for domain in DOMAINS}
    for entry in catalog["items"]:
        domain = entry["domain"]
        by_key.setdefault(domain, {})
        for key in entry.get("lookup_keys", []):
            by_key[domain].setdefault(key, []).append(entry["id"])
    return by_key


def emit_indexes(catalog: dict[str, Any], out_dir: Path) -> None:
    """3개 inverted index를 indexes/ 하위에 저장."""
    indexes_dir = out_dir / "catalog" / "indexes"
    _ensure_dir(indexes_dir)
    _write_json(indexes_dir / "by_id.json", build_by_id_index(catalog))
    _write_json(indexes_dir / "by_alias.json", build_by_alias_index(catalog))
    _write_json(indexes_dir / "by_lookup_key.json", build_by_lookup_key_index(catalog))


def emit_pickle(catalog: dict[str, Any], out_dir: Path) -> int:
    """Single-file pickle with all dicts for fast load (~5ms target).

    Returns bytes written.
    """
    pickle_path = out_dir / "catalog.pickle"
    _ensure_dir(pickle_path.parent)
    by_domain = split_by_domain(catalog)
    payload = {
        "schema_version": catalog.get("schema_version"),
        "catalog_version": catalog.get("catalog_version"),
        "generated_at": catalog.get("generated_at"),
        "source": catalog.get("source"),
        "domains": catalog.get("domains"),
        "items": catalog["items"],
        "by_domain_items": by_domain,
        "aliases": catalog.get("aliases", []),
        "standards_mappings": catalog.get("standards_mappings", []),
        "by_id": build_by_id_index(catalog),
        "by_alias": build_by_alias_index(catalog),
        "by_lookup_key": build_by_lookup_key_index(catalog),
    }
    with pickle_path.open("wb") as fp:
        pickle.dump(payload, fp, protocol=pickle.HIGHEST_PROTOCOL)
    return pickle_path.stat().st_size


def emit_source_hashes(skill_dir: Path, out_dir: Path) -> int:
    """references/ 하위 모든 .md 파일의 sha256 해시를 저장. Returns hash count."""
    refs = skill_dir / "references"
    hashes: dict[str, str] = {}
    for path in sorted(refs.rglob("*.md")):
        rel = path.relative_to(skill_dir).as_posix()
        with path.open("rb") as fp:
            digest = hashlib.sha256(fp.read()).hexdigest()
        hashes[rel] = digest
    source_path = out_dir / "source-hashes.json"
    _ensure_dir(source_path.parent)
    _write_json(
        source_path,
        {
            "generated_at": generated_at(),
            "algorithm": "sha256",
            "count": len(hashes),
            "hashes": hashes,
        },
    )
    return len(hashes)


def emit_state(skill_dir: Path, catalog: dict[str, Any], state_dir: Path) -> dict[str, Any]:
    """모든 state 산출물 emit + summary 반환."""
    _ensure_dir(state_dir / "catalog")
    shard_counts = emit_domain_shards(catalog, state_dir)
    emit_meta(catalog, state_dir, shard_counts)
    emit_aliases(catalog, state_dir)
    emit_standards(catalog, state_dir)
    emit_indexes(catalog, state_dir)
    pickle_bytes = emit_pickle(catalog, state_dir)
    hash_count = emit_source_hashes(skill_dir, state_dir)
    return {
        "shard_counts": shard_counts,
        "pickle_bytes": pickle_bytes,
        "hash_count": hash_count,
        "state_dir": str(state_dir),
    }


def verify_source_hashes(skill_dir: Path, state_dir: Path) -> list[str]:
    """source-hashes.json이 실제 markdown 해시와 일치하는지 확인."""
    issues: list[str] = []
    source_path = state_dir / "source-hashes.json"
    if not source_path.exists():
        return [f"missing source-hashes.json: {source_path}"]
    try:
        stored = json.loads(source_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return [f"corrupt source-hashes.json: {exc}"]
    stored_hashes: dict[str, str] = stored.get("hashes", {})

    actual_hashes: dict[str, str] = {}
    for path in sorted((skill_dir / "references").rglob("*.md")):
        rel = path.relative_to(skill_dir).as_posix()
        with path.open("rb") as fp:
            actual_hashes[rel] = hashlib.sha256(fp.read()).hexdigest()

    for rel, expected in stored_hashes.items():
        actual = actual_hashes.get(rel)
        if actual is None:
            issues.append(f"source-hash file missing: {rel}")
        elif actual != expected:
            issues.append(f"source-hash mismatch: {rel}")
    for rel in actual_hashes:
        if rel not in stored_hashes:
            issues.append(f"source-hash uncovered file: {rel}")
    return issues


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate dev-advisor catalog-index.json")
    parser.add_argument("--check", action="store_true", help="fail when catalog-index.json is stale")
    parser.add_argument("--output", default="catalog-index.json", help="output path relative to skill root")
    parser.add_argument("--pretty", action="store_true", default=True, help="write pretty deterministic JSON")
    parser.add_argument(
        "--state-dir",
        default="scripts/state",
        help="state directory for shards / indexes / pickle / source-hashes (relative to skill root)",
    )
    parser.add_argument(
        "--no-state",
        action="store_true",
        help="skip emitting scripts/state/ artifacts (legacy single-JSON mode)",
    )
    args = parser.parse_args()

    script_dir = Path(__file__).resolve().parent
    skill_dir = script_dir.parent
    output = Path(args.output)
    if not output.is_absolute():
        output = skill_dir / output
    state_dir = Path(args.state_dir)
    if not state_dir.is_absolute():
        state_dir = skill_dir / state_dir

    catalog = build_catalog(skill_dir)
    valid_anchors, broken_anchors = annotate_anchors(skill_dir, catalog)
    text = json.dumps(catalog, ensure_ascii=False, indent=2, sort_keys=False) + "\n"

    if args.check:
        if not output.exists():
            print(f"FATAL: missing {output}", file=sys.stderr)
            return 1
        existing = json.loads(output.read_text(encoding="utf-8"))
        if normalize_for_check(existing) != normalize_for_check(catalog):
            print(f"FATAL: stale {output}", file=sys.stderr)
            return 1
        # source-hashes 일치 여부도 함께 검증 (state dir이 존재할 때만)
        if (state_dir / "source-hashes.json").exists():
            hash_issues = verify_source_hashes(skill_dir, state_dir)
            if hash_issues:
                for issue in hash_issues[:50]:
                    print(f"FATAL: {issue}", file=sys.stderr)
                if len(hash_issues) > 50:
                    print(f"FATAL: ... {len(hash_issues) - 50} more", file=sys.stderr)
                return 1
        print(
            "catalog-index.json OK "
            f"({len(catalog['items'])} items, {len(catalog['aliases'])} aliases, "
            f"{len(catalog['standards_mappings'])} standards mappings)"
        )
        print(f"Anchor check: {valid_anchors + broken_anchors}/{valid_anchors + broken_anchors} valid ({broken_anchors} broken)")
        return 0

    output.write_text(text, encoding="utf-8")
    print(
        f"wrote {output} ({len(catalog['items'])} items, {len(catalog['aliases'])} aliases, "
        f"{len(catalog['standards_mappings'])} standards mappings)"
    )

    if not args.no_state:
        summary = emit_state(skill_dir, catalog, state_dir)
        total_items = sum(summary["shard_counts"].values())
        print(
            f"wrote {state_dir} (domains={total_items}, pickle={summary['pickle_bytes']/1024:.1f}KB, "
            f"source-hashes={summary['hash_count']})"
        )

    total_anchors = valid_anchors + broken_anchors
    print(f"Anchor check: {valid_anchors}/{total_anchors} valid ({broken_anchors} broken)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
