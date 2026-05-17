#!/usr/bin/env python3
"""Resolve dev-advisor catalog lookups from catalog-index.json only."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any


DOMAIN_ALIASES = {
    "pattern": "patterns",
    "patterns": "patterns",
    "algorithm": "algorithms",
    "algorithms": "algorithms",
    "language": "languages",
    "languages": "languages",
    "security": "security",
    "principle": "principles",
    "principles": "principles",
    "quality": "quality",
}


def strip_md(text: str) -> str:
    text = re.sub(r"`([^`]*)`", r"\1", text)
    text = re.sub(r"\[([^\]\n]+)\]\([^)]+\)", r"\1", text)
    text = re.sub(r"<[^>]+>", "", text)
    return text.strip()


def normalize_key(text: str) -> str:
    text = re.sub(r"<[^>]+>", "", strip_md(text))
    text = re.sub(r"[`*_~]", "", text).strip().lower()
    symbol_aliases = {
        "c++": "cplusplus",
        "c#": "csharp",
        "f#": "fsharp",
        "vb.net": "vb dotnet",
    }
    for source, target in symbol_aliases.items():
        text = text.replace(source, target)
    text = re.sub(r"[^\w\s\-\u3131-\u318E\uAC00-\uD7A3]+", " ", text)
    text = re.sub(r"\s+", "-", text)
    text = re.sub(r"-+", "-", text)
    return text.strip("-")


def load_catalog(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise SystemExit(f"FATAL: catalog-index.json not found: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def resolve_domain(value: str) -> str:
    domain = DOMAIN_ALIASES.get(value.strip().lower())
    if not domain:
        raise SystemExit(f"FATAL: unknown domain: {value}")
    return domain


def public_item(entry: dict[str, Any], *, resolved_from: str | None = None) -> dict[str, Any]:
    data = {
        "domain": entry["domain"],
        "id": entry["id"],
        "item_type": entry.get("item_type", "entry"),
        "title": entry["title"],
        "title_ko": entry.get("title_ko"),
        "category": entry["category"],
        "file": entry["file"],
        "anchor": entry["anchor"],
        "reference": f"{entry['file']}#{entry['anchor']}",
        "aliases": entry.get("aliases", []),
    }
    if resolved_from:
        data["resolved_from"] = resolved_from
    return data


def build_indexes(catalog: dict[str, Any], domain: str) -> tuple[dict[str, dict[str, Any]], dict[str, str]]:
    by_id = {entry["id"]: entry for entry in catalog["items"] if entry["domain"] == domain}
    aliases: dict[str, str] = {}
    for row in catalog["aliases"]:
        if row["domain"] != domain:
            continue
        aliases[normalize_key(row["alias"])] = row["target_id"]
        aliases[row["alias"].strip().lower()] = row["target_id"]
    return by_id, aliases


def resolve(catalog: dict[str, Any], domain: str, query: str) -> dict[str, Any]:
    by_id, aliases = build_indexes(catalog, domain)
    normalized = normalize_key(query)

    if query in by_id:
        return public_item(by_id[query], resolved_from="id")
    if normalized in by_id:
        return public_item(by_id[normalized], resolved_from="id")
    if normalized in aliases and aliases[normalized] in by_id:
        return public_item(by_id[aliases[normalized]], resolved_from="alias")
    if query.strip().lower() in aliases and aliases[query.strip().lower()] in by_id:
        return public_item(by_id[aliases[query.strip().lower()]], resolved_from="alias")

    for entry in by_id.values():
        if normalized in entry.get("lookup_keys", []):
            return public_item(entry, resolved_from="lookup_key")

    raise SystemExit(f"FATAL: not found: {domain}/{query}")


def search(catalog: dict[str, Any], domain: str, query: str, *, limit: int) -> list[dict[str, Any]]:
    normalized = normalize_key(query)
    results: list[tuple[int, dict[str, Any]]] = []
    for entry in catalog["items"]:
        if entry["domain"] != domain:
            continue
        keys = set(entry.get("lookup_keys", []))
        haystack = " ".join(
            str(part)
            for part in [entry["id"], entry["title"], entry.get("title_ko"), entry["category"], *entry.get("aliases", [])]
            if part
        )
        normalized_haystack = normalize_key(haystack)
        score = 0
        if normalized == entry["id"]:
            score = 100
        elif normalized in keys:
            score = 90
        elif any(key.startswith(normalized) for key in keys):
            score = 70
        elif normalized and normalized in normalized_haystack:
            score = 40
        if score:
            results.append((score, entry))
    results.sort(key=lambda row: (-row[0], row[1]["item_type"], row[1]["id"]))
    return [public_item(entry) for _, entry in results[:limit]]


def list_items(catalog: dict[str, Any], domain: str, *, item_type: str | None, category: str | None) -> list[dict[str, Any]]:
    results = []
    for entry in catalog["items"]:
        if entry["domain"] != domain:
            continue
        if item_type and entry.get("item_type", "entry") != item_type:
            continue
        if category and entry["category"] != category:
            continue
        results.append(public_item(entry))
    return sorted(results, key=lambda row: (row["item_type"], row["category"], row["id"]))


def public_standard(row: dict[str, Any], *, resolved_from: str | None = None) -> dict[str, Any]:
    data = {
        "standard": row["standard"],
        "section_id": row["section_id"],
        "code": row["code"],
        "title": row["title"],
        "coverage": row["coverage"],
        "references": row.get("references", []),
    }
    if resolved_from:
        data["resolved_from"] = resolved_from
    return data


def resolve_standard(catalog: dict[str, Any], query: str, *, limit: int) -> list[dict[str, Any]]:
    normalized = normalize_key(query)
    exact: list[dict[str, Any]] = []
    partial: list[dict[str, Any]] = []
    for row in catalog.get("standards_mappings", []):
        keys = set(row.get("lookup_keys", []))
        code = normalize_key(row["code"])
        standard = normalize_key(row["standard"])
        title = normalize_key(row["title"])
        if normalized == code or normalized in keys:
            exact.append(public_standard(row, resolved_from="lookup_key"))
            continue
        if normalized == standard or normalized == title:
            exact.append(public_standard(row, resolved_from="lookup_key"))
            continue
        haystack = " ".join([standard, code, title, *keys])
        if normalized and normalized in haystack:
            partial.append(public_standard(row, resolved_from="partial"))
    results = exact + partial
    if not results:
        raise SystemExit(f"FATAL: standard not found: {query}")
    return results[:limit]


def main() -> int:
    parser = argparse.ArgumentParser(description="Lookup dev-advisor catalog-index.json")
    parser.add_argument("domain", help="pattern|algorithm|language|security|principle|quality|standard")
    parser.add_argument("command", help="list|search|<id-or-alias>")
    parser.add_argument("query", nargs="*", help="search query or optional list category")
    parser.add_argument("--catalog", default=None, help="catalog-index.json path")
    parser.add_argument("--type", dest="item_type", default=None, help="filter list by item_type")
    parser.add_argument("--limit", type=int, default=20, help="search result limit")
    args = parser.parse_args()

    script_dir = Path(__file__).resolve().parent
    catalog_path = Path(args.catalog) if args.catalog else script_dir.parent / "catalog-index.json"
    catalog = load_catalog(catalog_path)
    command = args.command.strip()
    if args.domain.strip().lower() in {"standard", "standards"}:
        query = " ".join([command, *args.query]).strip()
        output = resolve_standard(catalog, query, limit=args.limit)
    else:
        domain = resolve_domain(args.domain)
        if command == "list":
            category = " ".join(args.query).strip() or None
            output: Any = list_items(catalog, domain, item_type=args.item_type, category=category)
        elif command == "search":
            if not args.query:
                raise SystemExit("FATAL: search query required")
            output = search(catalog, domain, " ".join(args.query), limit=args.limit)
        else:
            query = " ".join([command, *args.query]).strip()
            output = resolve(catalog, domain, query)

    print(json.dumps(output, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
