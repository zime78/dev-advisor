# `full` 모드 — `audit --mode=serial` 별칭

`full`은 [`audit`](audit.md) 모드의 `--mode=serial` 별칭이다. 기존 호출자(`/dev-advisor full <module|path>`) 호환을 위해 유지된다.

신규 호출은 `audit --mode=serial`을 사용할 것.

## 매핑

| 기존 호출 | 신규 호출 (권장) |
|----------|----------------|
| `/dev-advisor full <module\|path>` | `/dev-advisor audit --mode=serial <module\|path>` |

## 절차·산출물

[`audit.md`](audit.md) `--mode=serial` 섹션 참조.
