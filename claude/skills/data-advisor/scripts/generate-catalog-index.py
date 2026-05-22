#!/usr/bin/env python3
"""Generate and verify data-advisor catalog-index.json (standalone, data domain only)."""
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

DOMAINS = ("patterns", "algorithms", "principles")
ENTRY_COUNT_KEYS = {
    "patterns": "EXPECTED_PATTERNS",
    "algorithms": "EXPECTED_ALGORITHMS",
    "principles": "EXPECTED_PRINCIPLES",
}


def strip_md(text: str) -> str:
    text = re.sub(r"`([^`]*)`", r"\1", text)
    text = re.sub(r"\[([^\]\n]+)\]\([^)]+\)", r"\1", text)
    text = re.sub(r"<[^>]+>", "", text)
    return text.strip()


def slugify(text: str) -> str:
    text = re.sub(r"<[^>]+>", "", text)
    text = re.sub(r"[`*_~]", "", text).strip().lower()
    text = re.sub(r"[^\w\s\-ㄱ-ㆎ가-힣]+", " ", text)
    text = re.sub(r"\s+", "-", text)
    text = re.sub(r"-+", "-", text)
    return text.strip("-")


def normalize_key(text: str) -> str:
    text = strip_md(text).lower()
    return slugify(text)


def build_lookup_keys(keys: list[str]) -> list[str]:
    return sorted({k for k in (normalize_key(k) for k in keys) if k})


def read_manifest(skill_dir: Path) -> dict[str, int]:
    path = skill_dir / ".counts.manifest"
    if not path.exists():
        raise SystemExit(f"FATAL: .counts.manifest not found at {path}")
    values: dict[str, int] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        m = re.match(r"^([A-Z0-9_]+)=(\d+)$", line.strip())
        if m:
            values[m.group(1)] = int(m.group(2))
    return values


def generated_at() -> str:
    epoch = os.environ.get("SOURCE_DATE_EPOCH")
    if epoch:
        dt = datetime.fromtimestamp(int(epoch), tz=timezone.utc)
    else:
        dt = datetime.now(tz=timezone.utc)
    return dt.replace(microsecond=0).isoformat().replace("+00:00", "Z")


def numbered_entries(path: Path) -> list[dict[str, Any]]:
    entries: list[dict[str, Any]] = []
    pending_anchor: str | None = None
    following_anchor_entry: int | None = None
    for line in path.read_text(encoding="utf-8").splitlines():
        if re.match(r"^##\s+\d+\.", line):
            inline_anchor = re.search(r'<a\s+id="([^"]+)"', line)
            m = re.match(r"^##\s+(\d+)\.\s+(.+?)\s*$", line)
            if not m:
                continue
            ordinal = int(m.group(1))
            raw_title = strip_md(m.group(2))
            title_ko = None
            ko_m = re.search(r"\(([^()]*[가-힣][^()]*)\)\s*$", raw_title)
            if ko_m:
                title_ko = ko_m.group(1).strip()
                raw_title = raw_title[:ko_m.start()].strip()
            heading_anchor = slugify(line.lstrip("#").strip())
            entries.append({
                "ordinal": ordinal,
                "title": raw_title,
                "title_ko": title_ko,
                "anchor": (inline_anchor.group(1) if inline_anchor else pending_anchor) or heading_anchor,
                "heading_anchor": heading_anchor,
            })
            following_anchor_entry = None if inline_anchor or pending_anchor else len(entries) - 1
            pending_anchor = None
            continue
        anchor_m = re.search(r'<a\s+id="([^"]+)"', line)
        if anchor_m:
            if following_anchor_entry is not None:
                entries[following_anchor_entry]["anchor"] = anchor_m.group(1)
                following_anchor_entry = None
            else:
                pending_anchor = anchor_m.group(1)
            continue
        if line.strip() and not line.startswith("<!--"):
            pending_anchor = None
            following_anchor_entry = None
    return entries


def collect_anchors(path: Path) -> set[str]:
    text = path.read_text(encoding="utf-8")
    anchors = set(re.findall(r'<a\s+id="([^"]+)"', text))
    for line in text.splitlines():
        m = re.match(r"^#{1,6}\s+(.+?)\s*$", line)
        if m:
            slug = slugify(m.group(1))
            if slug:
                anchors.add(slug)
                anchors.add(re.sub(r"^\d+-", "", slug))
    return anchors


def anchor_matches(fragment: str, anchors: set[str]) -> bool:
    return fragment in anchors or any(a.startswith(fragment + "-") for a in anchors)


def item(*, domain: str, item_id: str, title: str, title_ko: str | None,
         category: str, file_path: str, anchor: str,
         aliases: list[str] | None = None, item_type: str = "entry") -> dict[str, Any]:
    alias_list = sorted(set(aliases or []))
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
        "lookup_keys": build_lookup_keys(keys),
    }


def generate_domain(refs: Path, domain: str) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    for path in sorted((refs / domain).rglob("*.md")):
        if path.name == "index.md":
            continue
        category = path.with_suffix("").relative_to(refs / domain).as_posix()
        for entry in numbered_entries(path):
            item_id = re.sub(r"^\d+-", "", entry["anchor"] or entry["heading_anchor"])
            items.append(item(
                domain=domain,
                item_id=item_id,
                title=entry["title"],
                title_ko=entry["title_ko"],
                category=category,
                file_path=f"references/{domain}/{path.relative_to(refs / domain).as_posix()}",
                anchor=entry["anchor"],
            ))
    return items


def parse_alias_table(index_path: Path) -> list[dict[str, str]]:
    aliases: list[dict[str, str]] = []
    in_alias = False
    for line in index_path.read_text(encoding="utf-8").splitlines():
        if re.match(r"^## 별칭", line):
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
        if alias in {"별칭", "Alias"} or primary in {"Primary ID", "설명"} or set(alias) <= set("-: "):
            continue
        aliases.append({"alias": alias, "target_id": primary,
                        "domain": "data", "source": "references/index.md"})
    return aliases


def validate(skill_dir: Path, catalog: dict[str, Any], manifest: dict[str, int]) -> list[str]:
    issues: list[str] = []
    refs = skill_dir / "references"
    ids: dict[tuple[str, str], str] = {}
    anchors_cache: dict[Path, set[str]] = {}
    entry_counts = {d: 0 for d in DOMAINS}

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

    return issues


def build_catalog(skill_dir: Path) -> dict[str, Any]:
    refs = skill_dir / "references"
    manifest = read_manifest(skill_dir)
    items: list[dict[str, Any]] = []
    for domain in DOMAINS:
        items.extend(generate_domain(refs, domain))
    items.sort(key=lambda r: (r["domain"], r["category"], r["id"]))

    # aliases from references/index.md
    raw_aliases = parse_alias_table(refs / "index.md")
    ids_set = {(entry["domain"], entry["id"]) for entry in items}
    aliases_by_target: dict[tuple[str, str], list[str]] = {}
    for row in raw_aliases:
        for domain in DOMAINS:
            if (domain, row["target_id"]) in ids_set:
                aliases_by_target.setdefault((domain, row["target_id"]), []).append(row["alias"])
                row["domain"] = domain
                break
    for entry in items:
        entry["aliases"] = sorted(aliases_by_target.get((entry["domain"], entry["id"]), []))
        keys = [entry["id"], entry["title"], *entry["aliases"]]
        if entry.get("title_ko"):
            keys.append(entry["title_ko"])
        entry["lookup_keys"] = build_lookup_keys(keys)

    counts = {d: 0 for d in DOMAINS}
    for entry in items:
        if entry.get("item_type", "entry") == "entry":
            counts[entry["domain"]] += 1

    domains = {
        domain: {
            "index": f"references/{domain}/index.md",
            "expected_count": manifest.get(ENTRY_COUNT_KEYS[domain], 0),
            "actual_count": counts[domain],
        }
        for domain in DOMAINS
    }

    catalog = {
        "schema_version": "1.0",
        "catalog_version": "2026-05",
        "generated_at": generated_at(),
        "source": {"root": "references", "generator": "scripts/generate-catalog-index.py"},
        "domains": domains,
        "items": items,
        "aliases": [r for r in raw_aliases if r.get("domain") in DOMAINS],
    }

    issues = validate(skill_dir, catalog, manifest)
    if issues:
        for iss in issues[:50]:
            print(f"FATAL: {iss}", file=sys.stderr)
        raise SystemExit(1)
    return catalog


def normalize_for_check(catalog: dict[str, Any]) -> dict[str, Any]:
    n = copy.deepcopy(catalog)
    n["generated_at"] = "<ignored>"
    return n


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--output", default="catalog-index.json")
    args = parser.parse_args()

    script_dir = Path(__file__).resolve().parent
    skill_dir = script_dir.parent
    output = skill_dir / args.output

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
        print(f"catalog-index.json OK ({len(catalog['items'])} items, {len(catalog['aliases'])} aliases)")
        return 0

    output.write_text(text, encoding="utf-8")
    print(f"wrote {output} ({len(catalog['items'])} items, {len(catalog['aliases'])} aliases)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
