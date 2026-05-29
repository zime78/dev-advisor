#!/usr/bin/env python3
# check_anchor_resolution.py — Markdown 내부 링크/anchor 무결성 검증
#
# *.md 와 references/**/*.md, scripts/*.md 의 모든 내부 링크가 가리키는
# (a) 파일이 존재하는지, (b) anchor 가 실제 heading 또는 명시 anchor 와
# 매칭되는지 확인한다. fenced code block 과 inline code 안의 링크는 검증 대상에서 제외.
#
# Usage:
#   python3 check_anchor_resolution.py <skill_root>

import re
import sys
from pathlib import Path
from urllib.parse import unquote


def strip_fences(text: str) -> str:
    """검증 대상에서 fenced code block을 제거해 예제 링크 오탐을 막는다."""
    return re.sub(r"```.*?```", "", text, flags=re.S)


def strip_inline_code(text: str) -> str:
    """인라인 코드 안의 괄호/링크 모양 문자열을 검증 대상에서 제외한다."""
    return re.sub(r"`[^`]*`", "", text)


def slugify(heading: str) -> str:
    """GitHub Markdown과 유사한 방식으로 heading anchor 후보를 만든다."""
    heading = re.sub(r"<[^>]+>", "", heading)
    heading = re.sub(r"[`*_~]", "", heading).strip().lower()
    heading = re.sub(r"[^\w\s\-ㄱ-ㆎ가-힣]", "", heading)
    heading = re.sub(r"\s+", "-", heading)
    heading = re.sub(r"-+", "-", heading)
    return heading.strip("-")


anchor_cache: dict[Path, set[str]] = {}


def anchors_for(path: Path) -> set[str]:
    """파일의 명시적 anchor와 heading 기반 anchor를 수집해 캐시한다."""
    path = path.resolve()
    if path in anchor_cache:
        return anchor_cache[path]
    text = path.read_text(encoding="utf-8")
    anchors = set(re.findall(r'<a\s+id="([^"]+)"', text))
    for line in text.splitlines():
        m = re.match(r"^(#{1,6})\s+(.+?)\s*$", line)
        if m:
            slug = slugify(m.group(2))
            if slug:
                anchors.add(slug)
    anchor_cache[path] = anchors
    return anchors


def anchor_matches(fragment: str, anchors: set[str]) -> bool:
    """짧은 고정 fragment가 한국어 suffix heading anchor와 매칭되는지 확인한다."""
    if fragment in anchors:
        return True
    # Many catalog links intentionally use a stable short prefix for Korean-suffixed headings.
    return any(a.startswith(fragment + "-") for a in anchors)


def exists_in_file(md_file: Path, fragment: str) -> bool:
    """단일 markdown 파일에 anchor가 정확히 존재하는지 확인하는 외부 helper.

    다른 도구가 링크 생성 전에 anchor 유효성을 검증할 때 호출한다.
    메인 링크 검사기(anchor_matches)의 짧은 prefix 휴리스틱과 달리, 여기서는
    명시 anchor(`<a id>`) 또는 heading slug 와의 정확 매칭만 허용한다.
    짧은 fragment(예: '1')가 '1-...' heading 에 prefix 오탐 매칭되어
    false-positive 를 내는 것을 막기 위함이다.
    """
    md_file = md_file.resolve()
    if not md_file.exists():
        return False
    return fragment in anchors_for(md_file)


def _cli_exists() -> int:
    """`python3 -m check_anchor_resolution exists <file.md> <anchor>` 진입점."""
    if len(sys.argv) < 4:
        print(
            "Usage: check_anchor_resolution.py exists <file.md> <anchor>",
            file=sys.stderr,
        )
        return 2
    md_file = Path(sys.argv[2])
    anchor = sys.argv[3]
    return 0 if exists_in_file(md_file, anchor) else 1


def main() -> int:
    if len(sys.argv) >= 2 and sys.argv[1] == "exists":
        return _cli_exists()
    root = Path(sys.argv[1])
    check_files = sorted(
        set(root.glob("*.md"))
        | set((root / "references").rglob("*.md"))
        | set((root / "scripts").glob("*.md"))
    )

    link_re = re.compile(r"(?<!!)\[[^\]\n]+\]\(([^)\n]+)\)")
    issues: list[str] = []

    for src in check_files:
        if not src.exists():
            issues.append(f"{src.relative_to(root)}: missing checked file")
            continue
        raw_text = src.read_text(encoding="utf-8")
        text = strip_inline_code(strip_fences(raw_text))
        for match in link_re.finditer(text):
            raw_target = match.group(1).strip()
            line_no = text.count("\n", 0, match.start()) + 1
            target = raw_target.split()[0].strip("<>")
            if not target or target.startswith(("http://", "https://", "mailto:")):
                continue
            if "<" in raw_target or ">" in raw_target:
                continue
            if target == "./<lang>.md":
                continue
            path_part, _, fragment = target.partition("#")
            path_part = unquote(path_part)
            fragment = unquote(fragment)
            if path_part and not path_part.endswith(".md"):
                continue
            dest = src if not path_part else (src.parent / path_part).resolve()
            try:
                dest.relative_to(root)
            except ValueError:
                continue
            if not dest.exists():
                issues.append(
                    f"{src.relative_to(root)}:{line_no}: missing file -> {raw_target}"
                )
                continue
            if fragment and not anchor_matches(fragment, anchors_for(dest)):
                issues.append(
                    f"{src.relative_to(root)}:{line_no}: missing anchor -> {raw_target}"
                )

    if issues:
        for issue in issues[:50]:
            print("  - " + issue)
        if len(issues) > 50:
            print(f"  ... {len(issues) - 50} more")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
