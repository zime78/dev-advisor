# dev-advisor 워크플로우 인덱스

advisor 9 모드 + 보조 라우팅 + 공통 severity 정의의 진입점.

## 9 모드 (8 기본 + 1 통합)

| 모드 | 파일 | 1차 산출물 |
|------|------|-----------|
| `recommend`      | [`recommend.md`](recommend.md)             | 후보 매트릭스 3~5행 + Trade-off + 근거 |
| `validate`       | [`validate.md`](validate.md)               | 위반 항목 표 + 표준 인용 + P1/P2/P3 |
| `refactor`       | [`refactor.md`](refactor.md)               | 단계 표 + Before/After 코드 + 회귀 위험 |
| `maintain`       | [`maintain.md`](maintain.md)               | 코드 스멜 5 그룹 + 부채 표 + 우선순위 |
| `security-audit` | [`security-audit.md`](security-audit.md)   | STRIDE 6행 + DREAD + 컴플라이언스 |
| `qa`             | [`qa.md`](qa.md)                           | 요구사항 추적성 + 테스트 전략 + 릴리즈 준비도 + 프로세스 gap |
| `qc`             | [`qc.md`](qc.md)                           | 빌드/테스트 증거 + 결함 재현 + 품질 게이트 + 릴리즈 차단 증거 |
| `research`       | [`research.md`](research.md)               | 논문 매트릭스 + 카탈로그 cross-ref + 6 필드 + 3-source 교차 검증 |
| `audit` (`--mode=serial\|parallel`) | [`audit.md`](audit.md) | 7 모드 통합 + Top 10 + 단일 6 필드 (`serial` 순차 / `parallel` ULW + reviewer) |

Legacy aliases (호환 유지):

| 별칭 | 매핑 | 파일 |
|------|------|------|
| `full`  | `audit --mode=serial`   | [`full.md`](full.md) (stub) |
| `swarm` | `audit --mode=parallel` | [`swarm.md`](swarm.md) (stub) |

`research`는 `audit`에 미포함 (독립 모드 — 토큰 한계 + 외부 API 의존성 격리).

## 공통 자산

| 파일 | 용도 |
|------|------|
| [`_routing.md`](_routing.md)   | 라우팅 우선순위 + research 충돌 해소 + 라이프사이클 보조 + audit `--mode` 자동 라우팅 |
| [`_severity.md`](_severity.md) | 공통 severity 정규화 + audit 통합 우선순위 매트릭스 |

## 공통 6단계 + 6 필드

모든 모드는 동일한 6단계 (입력 수집 → 컨텍스트 분류 → 기준 매핑 → 분석/판정 → 6 필드 근거 산출 → 검증/후속) + 5단계 6 필드 (선택/판정 / 근거 (Why) / 대안 비교 / 표준 인용 / 적용 조건 / 6번째 필드 모드별 alias)를 따른다. 6번째 필드:

| 모드 | 6번째 필드 |
|------|-----------|
| `recommend` / `refactor` / `security-audit` | 비추천 조건 |
| `validate` | 예외·면제 조건 |
| `maintain` | 수용 가능 조건 |
| `qa` | 승인·면제 조건 |
| `qc` | 차단·재검증 조건 |
| `research` | 비추천 조건 (편향/시점/도메인 불일치) |
| `audit` (legacy `full` / `swarm`) | 비추천·예외·수용·품질 차단 통합 조건 |
