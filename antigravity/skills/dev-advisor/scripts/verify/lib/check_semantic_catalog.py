#!/usr/bin/env python3
# check_semantic_catalog.py — semantic index ↔ anchor ↔ standards mapping 의미 검증
#
# 검증 항목:
#   1. patterns/security index.md ID 매핑 -> 실제 anchor/heading 매칭
#   2. quality index.md fragment -> 실제 anchor 존재
#   3. principles 별칭 표 중복 체크
#   4. standards-mapping.md 참조 링크 + OWASP 섹션 4-1~4-4 + security 참조 존재
#   5. security/index.md "Semantic validation 후보" 섹션 존재
#   6. security-ai-model.md LLM 체크리스트 6항목 + cross-reference 3개 이상
#
# Usage:
#   python3 check_semantic_catalog.py <skill_root>

import re
import sys
from pathlib import Path


def strip_md(text: str) -> str:
    text = re.sub(r"`([^`]*)`", r"\1", text)
    text = re.sub(r"\[([^\]\n]+)\]\([^)]+\)", r"\1", text)
    text = re.sub(r"<[^>]+>", "", text)
    return text.strip()


def slugify(heading: str) -> str:
    heading = re.sub(r"<[^>]+>", "", heading)
    heading = re.sub(r"[`*_~]", "", heading).strip().lower()
    heading = re.sub(r"[^\w\s\-ㄱ-ㆎ가-힣]+", " ", heading)
    heading = re.sub(r"\s+", "-", heading)
    heading = re.sub(r"-+", "-", heading)
    return heading.strip("-")


def tokens(text: str) -> list[str]:
    return [token for token in slugify(text).split("-") if token]


anchor_cache: dict[Path, tuple[set[str], list[tuple[str, str]]]] = {}


def anchors_for(path: Path) -> tuple[set[str], list[tuple[str, str]]]:
    path = path.resolve()
    if path in anchor_cache:
        return anchor_cache[path]
    text = path.read_text(encoding="utf-8")
    anchors = set(re.findall(r'<a\s+id="([^"]+)"', text))
    headings: list[tuple[str, str]] = []
    for line in text.splitlines():
        match = re.match(r"^#{1,6}\s+(.+?)\s*$", line)
        if not match:
            continue
        slug = slugify(match.group(1))
        if slug:
            anchors.add(slug)
            anchors.add(re.sub(r"^\d+-", "", slug))
            headings.append((match.group(1), slug))
    anchor_cache[path] = (anchors, headings)
    return anchor_cache[path]


def anchor_matches(fragment: str, anchors: set[str]) -> bool:
    return fragment in anchors or any(
        anchor.startswith(fragment + "-") for anchor in anchors
    )


def mapping_row_matches(path: Path, item_id: str, name: str, ordinal: int) -> bool:
    if not path.exists():
        return False
    anchors, headings = anchors_for(path)
    candidates = {item_id, slugify(item_id), slugify(strip_md(name))}
    for candidate in candidates:
        if not candidate:
            continue
        if candidate in anchors:
            return True
        if any(
            anchor.startswith(candidate + "-") or anchor.endswith("-" + candidate)
            for anchor in anchors
        ):
            return True

    # 기존 카탈로그는 일부 항목에 명시 anchor가 없어서 `## N. English (Korean)`
    # heading anchor를 row 순서와 영문명 token으로 해석한다.
    for _, slug in headings:
        if not slug.startswith(f"{ordinal}-"):
            continue
        body_tokens = re.sub(r"^\d+-", "", slug).split("-")
        for source in (name, item_id):
            source_tokens = tokens(source)
            if source_tokens and all(token in body_tokens for token in source_tokens):
                return True
    return False


def parse_domain_mapping(
    refs: Path, domain: str, start_re: str, stop_re: str
) -> list[tuple[str, Path, str, int]]:
    index_path = refs / domain / "index.md"
    rows: list[tuple[str, Path, str, int]] = []
    current_file: str | None = None
    ordinal = 0
    in_mapping = False
    in_id_table = False
    for line in index_path.read_text(encoding="utf-8").splitlines():
        if re.match(start_re, line):
            in_mapping = True
            continue
        if in_mapping and re.match(stop_re, line):
            break
        if not in_mapping:
            continue
        section = re.match(
            r"^### .+?\(([A-Za-z0-9_./-]+\.md)(?:,[^)]*)?\).*$", line
        )
        if section:
            current_file = section.group(1)
            ordinal = 0
            in_id_table = False
            continue
        if re.match(r"^\|\s*ID\s*\|\s*영문명\s*\|", line):
            in_id_table = True
            continue
        if in_id_table and re.match(r"^\|[-: ]+\|", line):
            continue
        if in_id_table and not line.startswith("|"):
            in_id_table = False
            continue
        if not (current_file and in_id_table):
            continue
        row = re.match(r"^\|\s*`?([^`|]+?)`?\s*\|\s*(.*?)\s*\|", line)
        if not row:
            continue
        ordinal += 1
        rows.append(
            (
                strip_md(row.group(1)),
                refs / domain / current_file,
                strip_md(row.group(2)),
                ordinal,
            )
        )
    return rows


def main() -> int:
    root = Path(sys.argv[1])
    refs = root / "references"
    issues: list[str] = []
    warnings: list[str] = []

    def check_domain_mapping(domain: str, start_re: str, stop_re: str) -> int:
        rows = parse_domain_mapping(refs, domain, start_re, stop_re)
        seen: dict[str, list[str]] = {}
        for item_id, path, name, ordinal in rows:
            seen.setdefault(item_id, []).append(str(path.relative_to(refs)))
            if not mapping_row_matches(path, item_id, name, ordinal):
                issues.append(
                    f"{domain}/index.md: `{item_id}` -> {path.relative_to(refs)} anchor/heading 불일치"
                )
        for item_id, locations in sorted(seen.items()):
            if len(locations) > 1:
                issues.append(
                    f"{domain}/index.md: 중복 ID `{item_id}` ({', '.join(locations)})"
                )
        actual_anchor_count = 0
        indexed = set(seen)
        for path in (refs / domain).rglob("*.md"):
            if path.name == "index.md":
                continue
            anchors, _ = anchors_for(path)
            actual_anchor_count += len(anchors)
        if actual_anchor_count > len(indexed):
            warnings.append(
                f"{domain}: 실제 anchor/heading 후보 {actual_anchor_count}개, "
                f"index ID {len(indexed)}개 (미등재 anchor는 warning)"
            )
        return len(rows)

    patterns_rows = check_domain_mapping("patterns", r"^## 패턴 ID", r"^## 패턴 선택")
    security_rows = check_domain_mapping("security", r"^## 보안 ID", r"^## 표준 인용")

    def check_quality_mapping() -> int:
        rows: list[tuple[str, str, str]] = []
        index_path = refs / "quality" / "index.md"
        for line in index_path.read_text(encoding="utf-8").splitlines():
            row = re.match(
                r"^\|\s*`([^`]+)`\s*\|\s*\[[^\]]+\]\(([^)#]+\.md)#([^)]*)\)",
                line,
            )
            if row:
                rows.append((row.group(1), row.group(2), row.group(3)))
        seen: dict[str, list[str]] = {}
        for item_id, file_name, fragment in rows:
            seen.setdefault(item_id, []).append(file_name)
            path = refs / "quality" / file_name
            if item_id != fragment:
                issues.append(
                    f"quality/index.md: `{item_id}` 링크 fragment `{fragment}` 불일치"
                )
            if not path.exists() or not anchor_matches(fragment, anchors_for(path)[0]):
                issues.append(
                    f"quality/index.md: `{item_id}` -> {file_name}#{fragment} anchor 누락"
                )
        for item_id, locations in sorted(seen.items()):
            if len(locations) > 1:
                issues.append(
                    f"quality/index.md: 중복 ID `{item_id}` ({', '.join(locations)})"
                )
        return len(rows)

    quality_rows = check_quality_mapping()

    def check_principles_aliases() -> int:
        index_path = refs / "principles" / "index.md"
        aliases: dict[str, list[str]] = {}
        in_alias = False
        for line in index_path.read_text(encoding="utf-8").splitlines():
            if re.match(r"^### 별칭", line):
                in_alias = True
                continue
            if in_alias and line.startswith("## "):
                break
            if not in_alias:
                continue
            row = re.match(r"^\|\s*`?([^`|]+?)`?\s*\|\s*`?([^`|]+?)`?\s*\|", line)
            if not row:
                continue
            alias = strip_md(row.group(1))
            primary = strip_md(row.group(2))
            if alias == "별칭" or set(alias) <= set("-: "):
                continue
            aliases.setdefault(alias, []).append(primary)
        for alias, primaries in sorted(aliases.items()):
            if len(primaries) > 1:
                issues.append(
                    f"principles/index.md: 중복 별칭 `{alias}` ({', '.join(primaries)})"
                )
        return len(aliases)

    principles_alias_rows = check_principles_aliases()

    def check_standards_mapping() -> int:
        path = refs / "principles" / "standards-mapping.md"
        text = path.read_text(encoding="utf-8")
        link_re = re.compile(
            r"`((?:security|patterns|principles|quality)/[^`\s,)]+\.md)(?:#([^`\s,)]+))?`"
        )
        checked = 0
        for match in link_re.finditer(text):
            rel = match.group(1)
            fragment = match.group(2)
            dest = refs / rel
            checked += 1
            if not dest.exists():
                issues.append(f"principles/standards-mapping.md: 파일 누락 `{rel}`")
                continue
            if fragment and not anchor_matches(fragment, anchors_for(dest)[0]):
                issues.append(
                    f"principles/standards-mapping.md: anchor 누락 `{rel}#{fragment}`"
                )

        owasp_sections = {
            "OWASP Web": r"^### 4-1\.",
            "OWASP API": r"^### 4-2\.",
            "OWASP Mobile": r"^### 4-3\.",
            "OWASP LLM": r"^### 4-4\.",
        }
        lines = text.splitlines()
        for label, start_re in owasp_sections.items():
            start = next(
                (i for i, line in enumerate(lines) if re.match(start_re, line)), None
            )
            if start is None:
                issues.append(f"principles/standards-mapping.md: {label} 섹션 누락")
                continue
            end = next(
                (
                    i
                    for i in range(start + 1, len(lines))
                    if re.match(r"^### 4-\d\.|^## 5\.", lines[i])
                ),
                len(lines),
            )
            section = "\n".join(lines[start:end])
            if not re.search(r"`security/[^`\s,)]+\.md", section):
                issues.append(
                    f"principles/standards-mapping.md: {label} 섹션 security reference 누락"
                )
        return checked

    standards_links = check_standards_mapping()

    security_index = refs / "security" / "index.md"
    if "## Semantic validation 후보" not in security_index.read_text(encoding="utf-8"):
        issues.append("security/index.md: `## Semantic validation 후보` 섹션 누락")

    def check_ai_llm_security() -> None:
        path = refs / "security" / "security-ai-model.md"
        text = path.read_text(encoding="utf-8")
        required_terms = [
            "Prompt Injection",
            "Tool Permission",
            "RAG / Vector DB",
            "Output Handling",
            "System Prompt Leakage",
            "Agent Audit / Evals",
        ]
        for term in required_terms:
            if term not in text:
                issues.append(
                    f"security/security-ai-model.md: LLM 체크리스트 문구 누락 `{term}`"
                )
        refs_required = [
            "security-authz",
            "security-data-protection",
            "security-api-web",
            "security-detect-respond",
            "patterns/ai-llm",
        ]
        ref_hits = sum(1 for token in refs_required if token in text)
        if ref_hits < 3:
            issues.append(
                f"security/security-ai-model.md: LLM 보안 cross-reference {ref_hits}개 (<3)"
            )

    check_ai_llm_security()

    print(
        f"patterns index rows={patterns_rows}, security index rows={security_rows}, "
        f"quality index rows={quality_rows}, principles aliases={principles_alias_rows}, "
        f"standards links={standards_links}"
    )
    for warning in warnings[:20]:
        print("WARN: " + warning)
    if len(warnings) > 20:
        print(f"WARN: ... {len(warnings) - 20} more")
    if issues:
        for issue in issues[:80]:
            print("FAIL: " + issue)
        if len(issues) > 80:
            print(f"FAIL: ... {len(issues) - 80} more")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
