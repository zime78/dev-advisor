#!/usr/bin/env python3
"""Resolve data-advisor catalog lookups from catalog-index.json."""
from __future__ import annotations
import argparse, json, re, sys
from pathlib import Path
from typing import Any

def normalize_key(text: str) -> str:
    text = re.sub(r"`([^`]*)`", r"\1", text)
    text = re.sub(r"<[^>]+>", "", text)
    text = re.sub(r"[`*_~]", "", text).strip().lower()
    text = re.sub(r"[^\w\s\-ㄱ-ㆎ가-힣]+", " ", text)
    text = re.sub(r"\s+", "-", text)
    return text.strip("-")

def load_catalog(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise SystemExit(f"FATAL: catalog-index.json not found: {path}")
    return json.loads(path.read_text(encoding="utf-8"))

def public_item(entry: dict[str, Any]) -> dict[str, Any]:
    return {
        "domain": entry["domain"], "id": entry["id"],
        "title": entry["title"], "title_ko": entry.get("title_ko"),
        "category": entry["category"], "file": entry["file"],
        "anchor": entry["anchor"],
        "reference": f"{entry['file']}#{entry['anchor']}",
        "aliases": entry.get("aliases", []),
    }

def resolve(catalog: dict[str, Any], query: str) -> dict[str, Any]:
    nq = normalize_key(query)
    # alias 먼저
    for row in catalog.get("aliases", []):
        if normalize_key(row["alias"]) == nq:
            target = row["target_id"]
            for entry in catalog["items"]:
                if entry["id"] == target:
                    return public_item(entry)
    # id / lookup_keys
    for entry in catalog["items"]:
        if entry["id"] == query or entry["id"] == nq:
            return public_item(entry)
        if nq in entry.get("lookup_keys", []):
            return public_item(entry)
    raise SystemExit(f"FATAL: not found: {query}")

def search(catalog: dict[str, Any], query: str, limit: int) -> list[dict[str, Any]]:
    nq = normalize_key(query)
    results = []
    for entry in catalog["items"]:
        haystack = normalize_key(" ".join(filter(None, [
            entry["id"], entry["title"], entry.get("title_ko",""), entry["category"]
        ])))
        if nq in haystack:
            results.append((0 if entry["id"] == nq else 1, entry))
    results.sort(key=lambda r: (r[0], r[1]["id"]))
    return [public_item(e) for _, e in results[:limit]]

def list_items(catalog: dict[str, Any], category: str | None) -> list[dict[str, Any]]:
    return sorted(
        [public_item(e) for e in catalog["items"]
         if not category or e["category"] == category],
        key=lambda r: (r["category"], r["id"])
    )

def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("command", help="list|search|<id>")
    parser.add_argument("query", nargs="*")
    parser.add_argument("--catalog", default=None)
    parser.add_argument("--limit", type=int, default=20)
    args = parser.parse_args()
    script_dir = Path(__file__).resolve().parent
    catalog_path = Path(args.catalog) if args.catalog else script_dir.parent / "catalog-index.json"
    catalog = load_catalog(catalog_path)
    cmd = args.command.strip()
    q = " ".join(args.query).strip()
    if cmd == "list":
        output = list_items(catalog, q or None)
    elif cmd == "search":
        if not q:
            raise SystemExit("FATAL: search query required")
        output = search(catalog, q, args.limit)
    else:
        output = resolve(catalog, " ".join([cmd, *args.query]).strip())
    print(json.dumps(output, ensure_ascii=False, indent=2))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
