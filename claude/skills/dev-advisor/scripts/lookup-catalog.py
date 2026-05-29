#!/usr/bin/env python3
"""Resolve dev-advisor catalog lookups (pickle-first, sharded-JSON-fallback, full-JSON-emergency).

Performance strategy (P2-d):
1) Try `scripts/state/catalog.pickle` (~5ms cold load)
2) Fall back to `scripts/state/catalog/{meta,domains/*,indexes/*,aliases,standards}.json`
3) Last resort: legacy `catalog-index.json` at skill root
4) Emergency: regenerate via `scripts/generate-catalog-index.py` on-the-fly
"""

from __future__ import annotations

import argparse
import hashlib
import json
import pickle
import re
import statistics
import subprocess
import sys
import time
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


def warn(msg: str) -> None:
    """경고를 stderr로 출력 (사용자 visible). 자가치유 시점 기록 목적."""
    print(f"WARN: {msg}", file=sys.stderr)


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
    text = re.sub(r"[^\w\s\-ㄱ-ㆎ가-힣]+", " ", text)
    text = re.sub(r"\s+", "-", text)
    text = re.sub(r"-+", "-", text)
    return text.strip("-")


# ---------------------------------------------------------------------------
# Loader (pickle → sharded JSON → full JSON → regenerate emergency)
# ---------------------------------------------------------------------------


def _skill_dir() -> Path:
    return Path(__file__).resolve().parent.parent


def _state_dir() -> Path:
    return _skill_dir() / "scripts" / "state"


def _legacy_catalog_path() -> Path:
    return _skill_dir() / "catalog-index.json"


def _load_pickle() -> dict[str, Any] | None:
    """1순위: pickle. 손상 시 None."""
    pickle_path = _state_dir() / "catalog.pickle"
    if not pickle_path.exists():
        return None
    try:
        with pickle_path.open("rb") as fp:
            return pickle.load(fp)
    except Exception as exc:  # noqa: BLE001 - pickle은 여러 타입의 예외를 던질 수 있음
        warn(f"pickle load failed: {exc}; falling back to JSON")
        return None


def _load_sharded_json() -> dict[str, Any] | None:
    """2순위: scripts/state/catalog/* JSON shards를 합쳐 catalog dict 재구성."""
    state = _state_dir()
    meta_path = state / "catalog" / "meta.json"
    if not meta_path.exists():
        return None
    try:
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
        domains_dir = state / "catalog" / "domains"
        items: list[dict[str, Any]] = []
        by_domain_items: dict[str, list[dict[str, Any]]] = {}
        for shard_path in sorted(domains_dir.glob("*.json")):
            shard = json.loads(shard_path.read_text(encoding="utf-8"))
            domain = shard["domain"]
            by_domain_items[domain] = shard.get("items", [])
            items.extend(shard.get("items", []))
        aliases = json.loads((state / "catalog" / "aliases.json").read_text(encoding="utf-8"))["aliases"]
        standards = json.loads((state / "catalog" / "standards.json").read_text(encoding="utf-8"))[
            "standards_mappings"
        ]
        # 사전계산 인덱스가 있으면 로드 (없어도 lookup에서 lazy build 가능)
        indexes_dir = state / "catalog" / "indexes"
        by_id = (
            json.loads((indexes_dir / "by_id.json").read_text(encoding="utf-8"))
            if (indexes_dir / "by_id.json").exists()
            else {}
        )
        by_alias = (
            json.loads((indexes_dir / "by_alias.json").read_text(encoding="utf-8"))
            if (indexes_dir / "by_alias.json").exists()
            else {}
        )
        by_lookup_key = (
            json.loads((indexes_dir / "by_lookup_key.json").read_text(encoding="utf-8"))
            if (indexes_dir / "by_lookup_key.json").exists()
            else {}
        )
        return {
            "schema_version": meta.get("schema_version"),
            "catalog_version": meta.get("catalog_version"),
            "generated_at": meta.get("generated_at"),
            "source": meta.get("source"),
            "domains": meta.get("domains"),
            "items": items,
            "by_domain_items": by_domain_items,
            "aliases": aliases,
            "standards_mappings": standards,
            "by_id": by_id,
            "by_alias": by_alias,
            "by_lookup_key": by_lookup_key,
        }
    except (json.JSONDecodeError, KeyError, OSError) as exc:
        warn(f"sharded JSON load failed: {exc}; falling back to full catalog-index.json")
        return None


def _load_full_json() -> dict[str, Any] | None:
    """3순위: 기존 catalog-index.json (backward compat)."""
    path = _legacy_catalog_path()
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        warn(f"full catalog JSON load failed: {exc}; attempting regeneration")
        return None


def _emergency_regenerate() -> dict[str, Any] | None:
    """4순위 (최후): generate-catalog-index.py를 subprocess로 실행."""
    script = Path(__file__).resolve().parent / "generate-catalog-index.py"
    if not script.exists():
        warn(f"generator missing: {script}")
        return None
    try:
        subprocess.run(
            ["python3", str(script)],
            check=True,
            capture_output=True,
            text=True,
            timeout=120,
        )
        return _load_pickle() or _load_sharded_json() or _load_full_json()
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired, OSError) as exc:
        warn(f"emergency regeneration failed: {exc}")
        return None


# ---------------------------------------------------------------------------
# Staleness detection (P3-b)
# ---------------------------------------------------------------------------


def _source_hashes_path() -> Path:
    return _state_dir() / "source-hashes.json"


def _sample_source_files() -> list[Path]:
    """staleness 빠른 진단용: manifest + references/ 샘플 5개 파일."""
    skill = _skill_dir()
    samples: list[Path] = []
    manifest = skill / ".counts.manifest"
    if manifest.exists():
        samples.append(manifest)
    refs = skill / "references"
    if refs.exists():
        # 도메인별 index.md 가 있으면 최우선 (stale 변화 빈도 높음)
        priority = [
            refs / "patterns" / "index.md",
            refs / "algorithms" / "index.md",
            refs / "languages" / "index.md",
            refs / "security" / "index.md",
            refs / "principles" / "index.md",
            refs / "quality" / "index.md",
        ]
        for path in priority:
            if path.exists():
                samples.append(path)
            if len(samples) >= 6:  # 1 manifest + 5 markdowns
                break
    return samples


def _hash_file(path: Path) -> str:
    h = hashlib.sha256()
    try:
        h.update(path.read_bytes())
    except OSError:
        return ""
    return h.hexdigest()


def detect_staleness() -> tuple[bool, list[str]]:
    """source-hashes.json 와 sample 파일 해시를 비교. 변경 발견 시 (True, [drift...])."""
    hashes_path = _source_hashes_path()
    if not hashes_path.exists():
        return False, ["source-hashes.json missing — no baseline to compare"]
    try:
        recorded = json.loads(hashes_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as exc:
        return True, [f"source-hashes.json unreadable: {exc}"]
    recorded_hashes = recorded.get("hashes", {})
    skill = _skill_dir()
    drift: list[str] = []
    for sample in _sample_source_files():
        rel = sample.relative_to(skill).as_posix()
        live = _hash_file(sample)
        baseline = recorded_hashes.get(rel)
        if baseline is None:
            # 베이스라인에 없는 sample은 staleness 신호로 보지 않음(새 파일일 수 있음)
            continue
        if live and live != baseline:
            drift.append(rel)
    return (len(drift) > 0), drift


def _auto_regenerate_silently() -> bool:
    """generate-catalog-index.py --silent 비동기 실행. 실패해도 silent return."""
    script = Path(__file__).resolve().parent / "generate-catalog-index.py"
    if not script.exists():
        return False
    try:
        # --silent 미지원이면 일반 실행해도 OK — fallback
        proc = subprocess.run(
            ["python3", str(script)],
            check=False,
            capture_output=True,
            text=True,
            timeout=120,
        )
        return proc.returncode == 0
    except (subprocess.TimeoutExpired, OSError):
        return False


def load_catalog(
    explicit_path: Path | None = None,
    *,
    auto_regen: bool = True,
) -> dict[str, Any]:
    """Public loader. explicit_path가 주어지면 legacy JSON 강제 로드.

    auto_regen=True일 때 stale 캐시를 감지하면 generator를 한 번 호출해 재생성한다.
    """
    if explicit_path is not None:
        if not explicit_path.exists():
            raise SystemExit(f"FATAL: catalog not found: {explicit_path}")
        try:
            return json.loads(explicit_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise SystemExit(f"FATAL: invalid catalog JSON: {explicit_path}: {exc}")

    if auto_regen:
        stale, drift_paths = detect_staleness()
        if stale and drift_paths:
            warn(
                "stale cache detected ("
                + ", ".join(drift_paths[:3])
                + "); attempting auto-regeneration"
            )
            _auto_regenerate_silently()
            # 실패해도 아래 fallback 체인이 기존 데이터로 동작

    catalog = _load_pickle() or _load_sharded_json() or _load_full_json() or _emergency_regenerate()
    if catalog is None:
        raise SystemExit(
            "FATAL: no catalog source available. "
            "Run scripts/generate-catalog-index.py to bootstrap."
        )
    return catalog


# ---------------------------------------------------------------------------
# Health report (P3-b)
# ---------------------------------------------------------------------------


def _count_broken_anchors_in_indexes() -> tuple[int, int]:
    """precomputed indexes를 사용해 anchor count + broken count 측정.

    pickle/JSON 캐시 안의 entry["anchor"]만 검사하므로 lightweight하다.
    """
    catalog = _load_pickle() or _load_sharded_json() or _load_full_json()
    if catalog is None:
        return 0, 0
    total = 0
    broken = 0
    # 같은 파일을 여러 entry가 공유 — heading slug 캐시
    text_cache: dict[Path, set[str]] = {}

    def _anchors_in(md_file: Path) -> set[str]:
        if md_file in text_cache:
            return text_cache[md_file]
        try:
            text = md_file.read_text(encoding="utf-8", errors="replace")
        except OSError:
            text_cache[md_file] = set()
            return text_cache[md_file]
        anchors: set[str] = set(re.findall(r'<a\s+id="([^"]+)"', text))
        for line in text.splitlines():
            slug = _slug_of_heading(line)
            if slug:
                anchors.add(slug)
        text_cache[md_file] = anchors
        return anchors

    for entry in catalog.get("items", []):
        anchor = entry.get("anchor")
        file_path = entry.get("file")
        if not anchor or not file_path:
            continue
        total += 1
        # catalog entry["file"]은 "references/<domain>/<file>.md" 형식 (skill_root 기준)
        # 또는 historic 데이터에서 "<domain>/<file>.md"일 수 있음.
        candidate = _skill_dir() / file_path
        if not candidate.exists():
            alt = _skill_dir() / "references" / file_path
            candidate = alt
        if not candidate.exists():
            broken += 1
            continue
        anchors = _anchors_in(candidate)
        if anchor in anchors:
            continue
        if any(a.startswith(anchor + "-") for a in anchors):
            continue
        broken += 1
    return total, broken


def _slug_of_heading(line: str) -> str:
    """generate-catalog-index.py 의 slugify와 동일 규칙으로 heading anchor를 추정."""
    m = re.match(r"^#{1,6}\s+(.+?)\s*$", line)
    if not m:
        return ""
    heading = m.group(1)
    heading = re.sub(r"<[^>]+>", "", heading)
    heading = re.sub(r"[`*_~]", "", heading).strip().lower()
    # generator semantics: 특수문자 (예: `/`, `(`, `)`) 를 공백으로 치환 (delete 아님)
    heading = re.sub(r"[^\w\s\-ㄱ-ㆎ가-힣]+", " ", heading)
    heading = re.sub(r"\s+", "-", heading)
    heading = re.sub(r"-+", "-", heading)
    return heading.strip("-")


def report_health() -> dict[str, Any]:
    """`--health` 진단 결과를 dict로 반환."""
    state = _state_dir()
    pickle_path = state / "catalog.pickle"
    shards_dir = state / "catalog" / "domains"
    hashes_path = _source_hashes_path()

    pickle_ok = pickle_path.exists()
    shards_present = shards_dir.exists() and any(shards_dir.glob("*.json"))
    hashes_present = hashes_path.exists()

    stale = False
    drift_files: list[str] = []
    if hashes_present:
        stale, drift_files = detect_staleness()

    anchor_total, anchor_broken = _count_broken_anchors_in_indexes()

    return {
        "pickle_exists": pickle_ok,
        "shards_exist": shards_present,
        "source_hashes_present": hashes_present,
        "source_hashes_fresh": hashes_present and not stale,
        "drift_files": drift_files[:10],
        "anchor_total": anchor_total,
        "anchor_broken": anchor_broken,
        "anchor_valid": anchor_total > 0 and anchor_broken == 0,
    }


# ---------------------------------------------------------------------------
# Index helpers (precomputed when available, lazy fallback otherwise)
# ---------------------------------------------------------------------------


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


def _domain_items(catalog: dict[str, Any], domain: str) -> list[dict[str, Any]]:
    """도메인 items 리스트. precomputed by_domain_items 우선, 없으면 필터링."""
    by_domain_items = catalog.get("by_domain_items")
    if by_domain_items and domain in by_domain_items:
        return by_domain_items[domain]
    return [entry for entry in catalog["items"] if entry["domain"] == domain]


def build_indexes(catalog: dict[str, Any], domain: str) -> tuple[dict[str, dict[str, Any]], dict[str, str]]:
    """precomputed index가 있으면 O(1) 접근, 없으면 기존 동작 유지."""
    items = _domain_items(catalog, domain)
    by_id_idx = catalog.get("by_id", {}).get(domain)
    if by_id_idx:
        by_id = {entry_id: items[idx] for entry_id, idx in by_id_idx.items() if idx < len(items)}
    else:
        by_id = {entry["id"]: entry for entry in items}

    by_alias_idx = catalog.get("by_alias", {}).get(domain)
    if by_alias_idx:
        aliases = dict(by_alias_idx)
    else:
        aliases = {}
        for row in catalog.get("aliases", []):
            if row["domain"] != domain:
                continue
            aliases[normalize_key(row["alias"])] = row["target_id"]
            aliases[row["alias"].strip().lower()] = row["target_id"]
    return by_id, aliases


def resolve(catalog: dict[str, Any], domain: str, query: str) -> dict[str, Any]:
    by_id, aliases = build_indexes(catalog, domain)
    normalized = normalize_key(query)
    query_lower = query.strip().lower()

    if query in by_id:
        return public_item(by_id[query], resolved_from="id")
    if normalized in by_id:
        return public_item(by_id[normalized], resolved_from="id")
    if normalized in aliases and aliases[normalized] in by_id:
        return public_item(by_id[aliases[normalized]], resolved_from="alias")
    if query_lower in aliases and aliases[query_lower] in by_id:
        return public_item(by_id[aliases[query_lower]], resolved_from="alias")

    # precomputed by_lookup_key가 있으면 O(1) 조회
    by_lookup = catalog.get("by_lookup_key", {}).get(domain)
    if by_lookup and normalized in by_lookup:
        target_ids = by_lookup[normalized]
        for target_id in target_ids:
            if target_id in by_id:
                return public_item(by_id[target_id], resolved_from="lookup_key")

    # fallback: lookup_keys 직접 스캔
    for entry in by_id.values():
        if normalized in entry.get("lookup_keys", []):
            return public_item(entry, resolved_from="lookup_key")

    raise SystemExit(f"FATAL: not found: {domain}/{query}")


def search(catalog: dict[str, Any], domain: str, query: str, *, limit: int) -> list[dict[str, Any]]:
    normalized = normalize_key(query)
    results: list[tuple[int, dict[str, Any]]] = []
    for entry in _domain_items(catalog, domain):
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


def list_items(
    catalog: dict[str, Any], domain: str, *, item_type: str | None, category: str | None
) -> list[dict[str, Any]]:
    results = []
    for entry in _domain_items(catalog, domain):
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


# ---------------------------------------------------------------------------
# Benchmark
# ---------------------------------------------------------------------------


def run_benchmark(runs: int = 100) -> dict[str, float]:
    """100회 lookup 시뮬레이션 + avg/p50/p99 측정."""
    queries = [
        ("principles", "srp"),
        ("patterns", "singleton"),
        ("algorithms", "quick-sort"),
        ("languages", "python"),
        ("security", "oauth2-pkce"),
        ("principles", "lsp"),
        ("patterns", "observer"),
        ("algorithms", "bfs"),
        ("principles", "dip"),
        ("quality", "qa-test-strategy"),
    ]

    # Cold load (포함하지 않음 — 캐시 비교 목적)
    load_start = time.perf_counter()
    catalog = load_catalog()
    load_ms = (time.perf_counter() - load_start) * 1000

    timings: list[float] = []
    for i in range(runs):
        domain, query = queries[i % len(queries)]
        start = time.perf_counter()
        try:
            resolve(catalog, domain, query)
        except SystemExit:
            pass
        timings.append((time.perf_counter() - start) * 1000)

    timings.sort()
    avg = statistics.mean(timings)
    p50 = timings[len(timings) // 2]
    p99 = timings[min(len(timings) - 1, int(len(timings) * 0.99))]
    return {
        "runs": runs,
        "load_ms": round(load_ms, 3),
        "avg_ms": round(avg, 3),
        "p50_ms": round(p50, 3),
        "p99_ms": round(p99, 3),
        "min_ms": round(min(timings), 3),
        "max_ms": round(max(timings), 3),
    }


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def main() -> int:
    parser = argparse.ArgumentParser(description="Lookup dev-advisor catalog (pickle-first)")
    parser.add_argument("domain", nargs="?", help="pattern|algorithm|language|security|principle|quality|standard")
    parser.add_argument("command", nargs="?", help="list|search|<id-or-alias>")
    parser.add_argument("query", nargs="*", help="search query or optional list category")
    parser.add_argument("--catalog", default=None, help="explicit catalog-index.json path (legacy mode)")
    parser.add_argument("--type", dest="item_type", default=None, help="filter list by item_type")
    parser.add_argument("--limit", type=int, default=20, help="search result limit")
    parser.add_argument("--benchmark", action="store_true", help="run 100-lookup benchmark and exit")
    parser.add_argument("--health", action="store_true", help="report cache/anchor health and exit")
    parser.add_argument(
        "--no-auto-regen",
        action="store_true",
        help="disable automatic catalog regeneration on stale cache",
    )
    args = parser.parse_args()

    if args.health:
        health = report_health()
        print(json.dumps(health, indent=2, ensure_ascii=False))
        # 1 if any critical signal off
        critical_ok = (
            health["pickle_exists"]
            and health["shards_exist"]
            and health["source_hashes_fresh"]
            and health["anchor_valid"]
        )
        return 0 if critical_ok else 1

    if args.benchmark:
        stats = run_benchmark()
        print(json.dumps(stats, indent=2))
        return 0

    if not args.domain or not args.command:
        parser.print_help()
        return 2

    catalog_path = Path(args.catalog) if args.catalog else None
    catalog = load_catalog(catalog_path, auto_regen=not args.no_auto_regen)
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
