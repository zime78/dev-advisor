# The Twelve-Factor App

Adam Wiggins (Heroku) 가 2011 년경 정리한 **클라우드 네이티브 SaaS / 웹 앱 운영 12 원칙**. 언어 / 프레임워크 / 백엔드 서비스에 비종속적이며, 선언적 셋업, 운영체제와의 깨끗한 계약, dev/prod 차이 최소화, 수평 확장을 목표로 한다.

**원전**:
- Adam Wiggins, *The Twelve-Factor App* (2011~), https://12factor.net
- Heroku Dev Center — Twelve-Factor App methodology

---

## 1. Codebase (코드베이스)

**정의**: "One codebase tracked in revision control, many deploys." — 버전 관리되는 *하나의* 코드베이스가 *다수의* 배포(dev / staging / prod) 를 만들어낸다.

**핵심 판단**: 앱 ↔ 코드베이스가 1:1 인가? 같은 코드에서 환경별 빌드가 갈라지는가? 여러 앱이 같은 코드를 공유하면 이미 위반 (라이브러리로 분리해야 함).

**특징 / 장점**:
- VCS(Git) 가 단일 진실원(SoT)
- 배포(deploy) = 같은 코드의 다른 실행 인스턴스
- 환경 차이는 Config(3 인자)로만 해결

**위반 사례**: prod 와 dev 가 다른 브랜치 / 다른 리포 (drift 발생).
**적용 사례**: GitHub monorepo, GitHub Actions 의 동일 ref 기반 멀티 배포.

**난이도**: 낮음 | **사용 빈도**: ★★★★★

```bash
# 준수: 하나의 코드베이스 → 환경별 배포
git tag v1.2.0           # prod 배포 태그
git push origin main     # dev 자동 배포 (CI/CD)
# .gitignore: .env, configs/*.local.ini  → secret 은 코드베이스에서 제외
```

**관련 원칙 / 패턴**: [12f-config](#3-config-설정), [patterns/deployment](../patterns/deployment.md), Trunk-Based Development, GitOps.

---

## 2. Dependencies (의존성)

**정의**: "Explicitly declare and isolate dependencies." — 의존성을 *명시적으로 선언* 하고 *격리* 한다.

**핵심 판단**: 시스템 패키지를 *암묵적으로* 끌어쓰지 않는가? `git clone` 직후 정해진 명령으로 모든 의존성을 받을 수 있는가? lockfile 이 커밋되어 있는가?

**특징 / 장점**:
- manifest 파일(`package.json`, `go.mod`, `requirements.txt`) 로 선언
- lockfile (`package-lock.json`, `go.sum`) 로 버전 고정
- 격리 도구 (virtualenv, npm 로컬, Docker) 로 호스트 누출 차단

**위반 사례**: `apt install` 된 system Python 만 동작, 다른 머신에서 실패.
**적용 사례**: Node `package.json` + `npm ci`, Go `go.mod` + vendoring.

**난이도**: 낮음 | **사용 빈도**: ★★★★★

```go
// go.mod — 준수 (격리 + 명시)
module github.com/example/myapp
go 1.22
require (
    github.com/gin-gonic/gin v1.10.0
    github.com/go-sql-driver/mysql v1.8.1
)
```

**관련 원칙 / 패턴**: [12f-build-release-run](#5-build-release-run-빌드-릴리스-실행), SBOM, [security/security-platform](../security/security-platform.md).

---

## 3. Config (설정)

**정의**: "Store config in the environment." — 환경에 따라 달라지는 설정은 *환경변수* 로 저장한다.

**핵심 판단**: DB URL · API key · 자격증명을 코드에서 분리했는가? 같은 빌드 산출물이 환경변수만 바꿔 dev/staging/prod 에서 동작 가능한가?

**특징 / 장점**:
- 코드와 설정의 명확한 분리 (오픈소스화 안전)
- 환경별 그룹화 없이 *환경변수 1 개 단위* 로 변경
- 12-factor 가장 자주 위반되는 인자

**위반 사례**: `db_url = "mysql://root:pass@prod-db/app"` 하드코드.
**적용 사례**: `os.Getenv("DATABASE_URL")`, Spring `@Value`, AWS Secrets Manager 외부 주입.

**난이도**: 낮음 | **사용 빈도**: ★★★★★

```go
// 위반: 코드 안 secret
const dbURL = "postgres://admin:s3cret@prod.db:5432/app"

// 준수: 환경변수 주입
dbURL := os.Getenv("DATABASE_URL")
if dbURL == "" { log.Fatal("DATABASE_URL not set") }
```

**관련 원칙 / 패턴**: [dip](solid.md#5-dependency-inversion-principle-dip-의존-역전-원칙), [security/security-sdlc](../security/security-sdlc.md).

---

## 4. Backing Services (백엔드 서비스)

**정의**: "Treat backing services as attached resources." — DB / 캐시 / 큐 / 외부 API 같은 백엔드 서비스를 *연결 가능한 자원* 으로 다룬다.

**핵심 판단**: 로컬 MySQL ↔ AWS RDS 교체가 *코드 수정 없이* config 변경만으로 가능한가? 자원이 죽으면 재연결만으로 복구되는가?

**특징 / 장점**:
- "로컬 vs 서드파티" 구분 없음 — 모두 URL/credential 로 연결
- 자원 교체 비용 = config 변경 비용
- DI / Repository 패턴과 결합

**위반 사례**: 캐시 서버를 코드에서 직접 instance 화 (`new RedisClient("127.0.0.1")`).
**적용 사례**: `DATABASE_URL`, `REDIS_URL` 환경변수, Spring `DataSource` 빈 주입.

**난이도**: 낮음~중간 | **사용 빈도**: ★★★★★

```python
# 준수: URL 한 줄 교체로 로컬 ↔ 클라우드 전환
import os
from sqlalchemy import create_engine
engine = create_engine(os.environ["DATABASE_URL"])
```

**관련 원칙 / 패턴**: [dip](solid.md#5-dependency-inversion-principle-dip-의존-역전-원칙), Repository, Adapter, [patterns/reliability](../patterns/reliability.md).

---

## 5. Build, Release, Run (빌드, 릴리스, 실행)

**정의**: "Strictly separate build and run stages." — *빌드 → 릴리스 → 실행* 3 단계를 명확히 분리한다.

**핵심 판단**: 빌드 산출물은 *불변(immutable)* 인가? 릴리스 = 빌드 + config 결합 + 고유 ID. 실행 단계에서 코드 변경 불가.

**특징 / 장점**:
- Build: 코드 → artifact (jar, docker image, binary)
- Release: artifact + 환경 config → 고유 release ID (예: timestamp + git sha)
- Run: release 를 실행 환경에 띄움
- 롤백 = 이전 release 재실행

**위반 사례**: prod 서버에 SSH 로 hot-fix 패치.
**적용 사례**: Docker multi-stage build, GitHub Actions / GitLab CI pipeline.

**난이도**: 중간 | **사용 빈도**: ★★★★★

```dockerfile
# Build → Run 분리 (multi-stage). 빌드 산출물은 불변, 실행은 env 로 config 주입.
FROM golang:1.22 AS builder
WORKDIR /src
COPY . .
RUN go build -o /out/server ./cmd/server          # Build
FROM gcr.io/distroless/static
COPY --from=builder /out/server /server
ENTRYPOINT ["/server"]                             # Run
```

**관련 원칙 / 패턴**: [12f-dev-prod-parity](#10-devprod-parity-개발운영-환경-일치), Immutable Infrastructure, GitOps.

---

## 6. Processes (프로세스)

**정의**: "Execute the app as one or more stateless processes." — 앱은 *무상태* 프로세스 하나 이상으로 실행되며, 영속 데이터는 backing service 에만 저장한다.

**핵심 판단**: 프로세스를 임의로 죽이고 재시작해도 사용자 영향 없는가? 세션 / 업로드 파일을 *프로세스 메모리 / 로컬 디스크* 에 두면 위반.

**특징 / 장점**:
- "share-nothing" 프로세스 → 수평 확장 가능
- sticky session 불필요
- 컨테이너 / Kubernetes pod 의 교체 가능성 전제

**위반 사례**: 사용자 업로드를 `/var/uploads` 로컬 디스크에 저장, 인메모리 세션.
**적용 사례**: 세션 → Redis / JWT 외부화, 업로드 → S3 / MinIO.

**난이도**: 중간 | **사용 빈도**: ★★★★★

```javascript
// 위반: 메모리 세션 → 재시작 시 소실
const sessions = {};

// 준수: Redis 세션 (외부 stateful 자원)
import session from 'express-session';
import RedisStore from 'connect-redis';
app.use(session({ store: new RedisStore({ client }), secret: process.env.SESSION_SECRET }));
```

**관련 원칙 / 패턴**: [12f-concurrency](#8-concurrency-동시성), [12f-disposability](#9-disposability-폐기-가능성), [patterns/concurrency](../patterns/concurrency.md).

---

## 7. Port Binding (포트 바인딩)

**정의**: "Export services via port binding." — 앱은 *자체적으로* HTTP / TCP 포트를 바인딩해 서비스를 노출한다.

**핵심 판단**: Apache / Nginx / Tomcat 런타임에 *내장* 되어서만 동작하는가? 앱이 standalone 으로 포트를 열고 들을 수 있는가?

**특징 / 장점**:
- 앱이 자체완결적 서비스 (self-contained)
- 다른 앱의 backing service 로 쉽게 노출
- 컨테이너 / serverless 와 자연 결합

**위반 사례**: Tomcat WAR 배포 전제로 앱 단독 실행 불가.
**적용 사례**: Node `app.listen(PORT)`, Go `http.ListenAndServe`, Spring Boot embedded Tomcat.

**난이도**: 낮음 | **사용 빈도**: ★★★★★

```go
// Go — Port 환경변수 + ListenAndServe
port := os.Getenv("PORT")
if port == "" { port = "8080" }
log.Fatal(http.ListenAndServe(":"+port, mux))
```

**관련 원칙 / 패턴**: [12f-backing-services](#4-backing-services-백엔드-서비스), Sidecar, Service Mesh.

---

## 8. Concurrency (동시성)

**정의**: "Scale out via the process model." — *프로세스 모델* 로 수평 확장한다. 워크로드 종류별로 다른 프로세스 타입(web / worker / scheduler) 을 정의.

**핵심 판단**: 부하 증가 시 수직 확장이 아니라 *프로세스 수* 를 늘려 해결되는가? UNIX process / 컨테이너 / pod 단위 scale-out 가능한가?

**특징 / 장점**:
- Procfile (Heroku) / Kubernetes Deployment replica 모델
- 각 프로세스 타입은 stateless (6 인자 의존)
- 워크로드 별로 독립 스케일링

**위반 사례**: web / worker 가 한 binary 안에 섞여 따로 스케일 불가.
**적용 사례**: `kubectl scale deploy/web --replicas=10`.

**난이도**: 중간 | **사용 빈도**: ★★★★☆

```bash
# Procfile — 워크로드 종류별 프로세스
# web: node server.js   /   worker: node worker.js   /   scheduler: node cron.js

# Kubernetes — replica 로 수평 확장
kubectl scale deploy/web --replicas=10
```

**관련 원칙 / 패턴**: [12f-processes](#6-processes-프로세스), [patterns/concurrency](../patterns/concurrency.md), Worker Pool.

---

## 9. Disposability (폐기 가능성)

**정의**: "Maximize robustness with fast startup and graceful shutdown." — 빠른 *기동* 과 *우아한 종료* 로 견고함을 극대화한다.

**핵심 판단**: 프로세스가 수 초 안에 기동하는가? `SIGTERM` 받으면 새 요청을 거부하고 진행 중 요청을 마무리한 뒤 종료하는가? `SIGKILL` 강제 종료에도 데이터 일관성이 깨지지 않는가?

**특징 / 장점**:
- 빠른 scale-out / 빠른 배포
- 노드 장애 시 다른 노드로 즉시 교체
- 큐 작업의 멱등성과 결합

**위반 사례**: `SIGTERM` 무시 → Kubernetes 가 30 초 후 `SIGKILL` 로 진행 중 작업 손실.
**적용 사례**: Go `http.Server.Shutdown(ctx)`, Kubernetes `preStop` hook.

**난이도**: 중간~높음 | **사용 빈도**: ★★★★☆

```go
// SIGTERM 수신 시 graceful shutdown
srv := &http.Server{Addr: ":8080", Handler: mux}
go func() { srv.ListenAndServe() }()

sigCh := make(chan os.Signal, 1)
signal.Notify(sigCh, syscall.SIGINT, syscall.SIGTERM)
<-sigCh
ctx, cancel := context.WithTimeout(context.Background(), 30*time.Second)
defer cancel()
srv.Shutdown(ctx)   // 진행 중 요청 30 초 대기
```

**관련 원칙 / 패턴**: [12f-processes](#6-processes-프로세스), [patterns/reliability](../patterns/reliability.md), Idempotent Consumer.

---

## 10. Dev/Prod Parity (개발/운영 환경 일치)

**정의**: "Keep development, staging, and production as similar as possible." — 개발 / 스테이징 / 운영 환경을 *최대한 비슷하게* 유지한다.

**핵심 판단**: time / personnel / tools 3 개의 gap 을 줄였는가? dev 와 prod 가 같은 backing service(DB 종류, 버전, OS) 를 쓰는가?

**특징 / 장점**:
- "내 컴퓨터에선 되는데" 문제 차단
- 같은 Docker image 가 dev/staging/prod 모두에서 동작
- 배포 주기 단축

**위반 사례**: dev = SQLite, prod = PostgreSQL → SQL 방언 차이로 prod 만 실패.
**적용 사례**: `docker-compose.dev.yml` ↔ `docker-compose.release.yml` 같은 image base. 본 프로젝트(jira-auto-analyze) 는 dev/release 가 동일 docker image, 포트만 분리.

**난이도**: 중간 | **사용 빈도**: ★★★★★

```yaml
# docker-compose.dev.yml — prod 와 동일한 base image
services:
  server:
    image: jira-auto-analyze-server:dev   # 같은 Dockerfile 빌드
    environment: { DATABASE_URL: postgres://db:5432/app, LOG_LEVEL: debug }
  db:
    image: postgres:16-alpine             # prod 도 동일 버전
```

**관련 원칙 / 패턴**: [12f-build-release-run](#5-build-release-run-빌드-릴리스-실행), [patterns/deployment](../patterns/deployment.md), Infrastructure as Code.

---

## 11. Logs (로그)

**정의**: "Treat logs as event streams." — 로그를 *이벤트 스트림* 으로 다룬다. 앱은 로그 파일 위치 / 보관 / 라우팅에 관여하지 않는다.

**핵심 판단**: 앱이 `stdout` 으로만 흘려보내고 *외부 수집기* (Fluent Bit / Vector / Loki / Datadog) 가 받아가는가? 앱이 로그 파일 경로를 알면 위반.

**특징 / 장점**:
- 앱은 단순히 `stdout` write → 책임 분리
- 컨테이너 / Kubernetes 표준 로그 패턴
- 구조화 로그(JSON) + 검색 시스템과 결합

**위반 사례**: 앱이 `/var/log/myapp/app.log` 에 직접 기록 + rotation 로직 내장.
**적용 사례**: 구조화 로그 `{"ts":"...","level":"info","msg":"..."}` JSON 한 줄, Fluent Bit DaemonSet 수집.

**난이도**: 낮음 | **사용 빈도**: ★★★★★

```go
// 준수: stdout 만 — 라우팅은 수집기가 처리
logger := slog.New(slog.NewJSONHandler(os.Stdout, &slog.HandlerOptions{Level: slog.LevelInfo}))
logger.Info("login", "user", uid, "ip", ip)
```

수집 파이프라인: Fluent Bit DaemonSet 이 `/var/log/containers/*.log` 를 tail → Loki / Elasticsearch / CloudWatch 로 라우팅.

**관련 원칙 / 패턴**: [patterns/observability](../patterns/observability.md), OpenTelemetry, Structured Logging.

---

## 12. Admin Processes (관리 프로세스)

**정의**: "Run admin/management tasks as one-off processes." — 관리 태스크(DB 마이그레이션, REPL, 일회성 스크립트) 는 *일회성 프로세스* 로 실행한다.

**핵심 판단**: 관리 태스크가 *앱과 같은 코드베이스 / 같은 의존성 / 같은 release* 에서 실행되는가? 별도 SSH 로 다른 환경에서 실행하면 위반.

**특징 / 장점**:
- 마이그레이션 코드도 VCS 추적
- 같은 release 의 환경변수 / 의존성 사용
- 한 번 실행 후 종료

**위반 사례**: prod 서버에 직접 SSH → `mysql -u root` 로 수동 SQL 실행.
**적용 사례**: Django `python manage.py migrate`, Rails `bin/rails db:migrate`, `kubectl run` one-off. 본 프로젝트(jira-auto-analyze) `scripts/test-trigger.sh` 가 one-off CLI 로 dev Server 에 manual trigger 등록.

**난이도**: 낮음 | **사용 빈도**: ★★★★☆

```bash
# 준수: 같은 release image 로 one-off 실행
kubectl run migrator --rm -it --restart=Never \
    --image=myapp:v1.2.0 \
    --env="DATABASE_URL=$DATABASE_URL" \
    -- /app/bin/migrate up
```

**관련 원칙 / 패턴**: [12f-build-release-run](#5-build-release-run-빌드-릴리스-실행), [12f-codebase](#1-codebase-코드베이스), Database Migration.

---

### 12 인자 컴플라이언스 체크리스트

| # | 인자 | 검증 방법 | 위반 예시 |
|---|------|----------|----------|
| 1 | Codebase | `git remote -v` + 환경별 같은 ref 배포 확인 | dev/prod 가 다른 리포 |
| 2 | Dependencies | `npm ci` / `go mod verify` 통과 | system Python 의존 |
| 3 | Config | `grep -rE '(password\|secret\|key)\s*=' src/` 비어있음 | DB 비밀번호 하드코드 |
| 4 | Backing Services | URL 한 줄 교체로 자원 교체 가능 | `new RedisClient("127.0.0.1")` |
| 5 | Build/Release/Run | release ID 추적 + 빌드/실행 분리 | prod 서버 SSH hot-fix |
| 6 | Processes | 프로세스 임의 재시작 후 정상 | 메모리 세션 |
| 7 | Port Binding | `curl localhost:$PORT/health` 단독 동작 | Tomcat WAR 전제 |
| 8 | Concurrency | `kubectl scale --replicas=10` 후 정상 | 단일 거대 프로세스 |
| 9 | Disposability | `kill -TERM $PID` 후 진행 요청 마무리 | SIGTERM 무시 |
| 10 | Dev/Prod Parity | dev/prod 동일 image + 같은 DB 버전 | dev=SQLite, prod=PG |
| 11 | Logs | 앱 출력이 `stdout` JSON 한 줄 | 앱이 파일 rotation |
| 12 | Admin Processes | 같은 release image 로 one-off 실행 | 수동 prod SSH SQL |

---

## 표준 인용

- Adam Wiggins, *The Twelve-Factor App* (2011~), https://12factor.net
- Heroku Dev Center — Twelve-Factor App methodology
- *Beyond the Twelve-Factor App* (Kevin Hoffman, 2016) — 15 인자 확장판 (참조)
- CNCF Cloud Native Definition — 12-Factor 와 클라우드 네이티브의 관계
