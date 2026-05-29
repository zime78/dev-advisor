#!/usr/bin/env python3
# check_languages_quality.py — 75개 언어 reference 품질 게이트
#
# 검증 항목:
#   1. 언어 파일 수 == EXPECTED_LANGUAGES
#   2. `## 관련 문서` 섹션 존재
#   3. Markdown 링크 ≥ 3개
#   4. 외부 공식 문서 후보 링크 ≥ 2개
#   5. `## 실사용 예제` 섹션 + 코드 블록 ≥ 1개
#   6. 예제 단어 수 ≥ 25개
#
# Usage:
#   EXPECTED_LANGUAGES=75 python3 check_languages_quality.py <lang_dir>

import os
import re
import sys
from pathlib import Path


def main() -> int:
    lang_dir = Path(sys.argv[1])
    expected_langs = int(os.environ["EXPECTED_LANGUAGES"])
    files = sorted(
        p for p in lang_dir.glob("*.md") if p.name not in {"index.md", "domains.md"}
    )
    issues: list[str] = []

    if len(files) != expected_langs:
        issues.append(f"언어 파일 수 기대={expected_langs}, 실제={len(files)}")

    section_re = re.compile(r"(?ms)^## 실사용 예제\n(.*?)(?=^## |\Z)")
    link_re = re.compile(r"\[[^\]\n]+\]\(([^)\n]+)\)")
    fence_re = re.compile(r"```[A-Za-z0-9_#+.-]*\n.*?\n```", re.S)
    word_re = re.compile(r"[A-Za-z0-9_가-힣]+")

    for path in files:
        text = path.read_text(encoding="utf-8")
        rel = path.name
        if "## 관련 문서" not in text:
            issues.append(f"{rel}: `## 관련 문서` 누락")

        links = link_re.findall(text)
        external_links = [link for link in links if link.startswith(("https://", "http://"))]
        if len(links) < 3:
            issues.append(f"{rel}: Markdown 링크 {len(links)}개 (<3)")
        if len(external_links) < 2:
            issues.append(f"{rel}: 외부 공식 문서 후보 링크 {len(external_links)}개 (<2)")

        match = section_re.search(text)
        if not match:
            issues.append(f"{rel}: `## 실사용 예제` 섹션 누락")
            continue
        example = match.group(1).strip()
        if not fence_re.search(example):
            issues.append(f"{rel}: 실사용 예제 코드 블록 누락")
        words = word_re.findall(example)
        if len(words) < 25:
            issues.append(f"{rel}: 실사용 예제 단어 수 {len(words)}개 (<25)")

    if issues:
        for issue in issues:
            print(issue)
        return 1
    print(f"{expected_langs}개 언어 파일 품질 기준 통과")
    return 0


if __name__ == "__main__":
    sys.exit(main())
