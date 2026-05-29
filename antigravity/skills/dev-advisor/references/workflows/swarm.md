# `swarm` 모드 — `audit --mode=parallel` 별칭

`swarm`은 [`audit`](audit.md) 모드의 `--mode=parallel` 별칭이다. 기존 호출자(`/dev-advisor swarm <module|path>`) 호환을 위해 유지된다.

신규 호출은 `audit --mode=parallel`을 사용할 것.

## 매핑

| 기존 호출 | 신규 호출 (권장) |
|----------|----------------|
| `/dev-advisor swarm <module\|path>` | `/dev-advisor audit --mode=parallel <module\|path>` |

## 절차·산출물

[`audit.md`](audit.md) `--mode=parallel` 섹션 참조.
