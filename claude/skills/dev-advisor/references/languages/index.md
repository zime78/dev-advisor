<!-- markdownlint-disable MD013 -->

# 프로그래밍 언어 지식 인덱스

기준일: 2026-05-13

이 reference 는 dev-advisor 스킬의 프로그래밍 언어 카탈로그다. 디자인 패턴(`references/patterns/`)과 알고리즘(`references/algorithms/`)에 이어 세 번째 reference 카테고리로, 언어 선택·비교·분야별 추천을 다룬다. 최신 순위, 점유율, 채용 수요, 연봉, 릴리스 상태처럼 변동 가능한 정보는 답변 전에 웹으로 확인한다.

## 전체 흐름 요약

2026년 현재 큰 흐름은 Python이 AI, 데이터, 자동화, 백엔드에서 넓게 쓰이고, JavaScript/TypeScript가 웹과 앱 계층의 중심이라는 점이다. Java와 C#은 기업 시스템에서 강하고, C/C++는 시스템, 임베디드, 게임, 고성능 영역의 기반이다. Go는 클라우드와 인프라, Rust는 안전한 시스템 개발, SQL은 데이터 중심 개발의 필수 언어로 다룬다.

## 빠른 요약

| 목적 | 우선 검토할 언어 |
| --- | --- |
| 처음 배우기 | Python, JavaScript, SQL |
| 웹 프론트엔드 | JavaScript, TypeScript, HTML/CSS |
| 웹 백엔드 | TypeScript, Python, Java, C#, Go, PHP, Ruby |
| AI/데이터 | Python, SQL, R, Julia |
| 기업 시스템 | Java, C#, SQL, Python, COBOL, ABAP |
| 시스템/임베디드 | C, C++, Rust, Zig, Assembly, Ada |
| 모바일 | Kotlin, Swift, Dart, Objective-C |
| 게임 | C++, C#, Lua, GDScript |
| DevOps/클라우드 | Go, Python, Bash, PowerShell, HCL |
| 통계/과학계산 | Python, R, MATLAB, Julia, Fortran, SAS |

## 핵심 언어 우선순위

| 우선순위 | 언어 | 이유 |
| --- | --- | --- |
| 1 | Python | AI, 데이터, 자동화, 백엔드까지 범용성이 가장 높음 |
| 2 | JavaScript | 브라우저 표준 언어이며 웹 생태계의 기반 |
| 3 | TypeScript | 대형 웹앱과 AI 보조 개발 시대에 타입 안정성으로 성장 |
| 4 | SQL | 대부분의 서비스가 데이터베이스를 쓰기 때문에 필수 |
| 5 | Java | 엔터프라이즈 백엔드, 금융, 공공, Android 생태계 |
| 6 | C# | .NET, Windows, 기업 시스템, Unity 게임 |
| 7 | C | 운영체제, 펌웨어, 임베디드의 기반 |
| 8 | C++ | 게임엔진, 고성능 컴퓨팅, 시스템 소프트웨어 |
| 9 | Go | 클라우드 인프라, 서버, DevOps 도구 |
| 10 | Rust | 메모리 안전성과 성능을 동시에 요구하는 시스템 영역 |

## 선택 기준

언어를 선택할 때는 유행보다 **문제 영역, 팀 역량, 배포 환경, 생태계, 유지보수 기간**을 먼저 본다.

- AI/데이터 제품이면 Python과 SQL을 기본으로 두고, 통계 연구가 강하면 R을 추가한다.
- 웹 제품이면 TypeScript를 중심에 두고, 백엔드는 팀 경험에 따라 Node.js, Python, Java, C#, Go 중 선택한다.
- 대기업/금융/공공 시스템이면 Java, C#, SQL의 장기 유지보수성을 우선한다.
- 모바일 앱이면 Android는 Kotlin, iOS는 Swift, 단일 코드베이스가 중요하면 Flutter/Dart를 검토한다.
- 시스템/성능/임베디드라면 C/C++가 여전히 기본이고, 안전성이 중요하면 Rust를 검토한다.
- 클라우드 인프라 도구라면 Go, Python, Bash, HCL 조합이 실용적이다.

## 언어별 상세 파일 구성

각 언어 파일은 단순 소개가 아니라 선택과 비교에 필요한 실무 판단 항목을 포함한다. `/language <id>` 응답은 언어 선택, 도입 판단, 실무 예제, 공식 문서 연결까지 한 번에 제공하는 것을 기준으로 한다.

- 핵심 판단
- 사용처, 특징, 장점, 제약
- 적합한 프로젝트
- 부적합하거나 주의할 프로젝트
- 대표 생태계와 도구
- 학습 난이도와 선행 지식
- 운영/배포 관점
- 타입/런타임 특성
- 실사용 예제
- 관련 문서 (공식 문서/스펙/레퍼런스/패키지·툴링 문서)
- 비교 포인트와 함께 비교할 언어
- 도입 전 체크리스트
- 최신 확인 필요 항목

## 언어 파일 품질 기준

75개 언어 상세 파일은 다음 기준을 만족해야 한다.

- 모든 언어 파일은 `## 관련 문서` 섹션을 포함한다.
- 각 언어 파일은 Markdown 링크 3개 이상, 외부 공식 문서 후보 링크 2개 이상을 제공한다.
- `## 실사용 예제`는 코드 블록 1개 이상을 포함하고, hello-world 수준이 아니라 해당 언어의 강한 사용 영역을 보여준다.
- 예제 섹션은 최소 25단어 이상으로 실무 맥락을 설명한다.
- 위 기준은 `scripts/verify-references.sh`의 languages 품질 게이트에서 강제한다.

## 상세 언어 파일

- [Python](./python.md)
- [JavaScript](./javascript.md)
- [TypeScript](./typescript.md)
- [SQL](./sql.md)
- [Java](./java.md)
- [C#](./csharp.md)
- [C](./c.md)
- [C++](./cplusplus.md)
- [Go](./go.md)
- [Rust](./rust.md)
- [PHP](./php.md)
- [Kotlin](./kotlin.md)
- [Swift](./swift.md)
- [Dart](./dart.md)
- [Ruby](./ruby.md)
- [R](./r.md)
- [Bash/Shell](./bash-shell.md)
- [PowerShell](./powershell.md)
- [Scala](./scala.md)
- [Lua](./lua.md)
- [Objective-C](./objective-c.md)
- [Perl](./perl.md)
- [Groovy](./groovy.md)
- [Visual Basic .NET](./visual-basic-dotnet.md)
- [VBA](./vba.md)
- [MATLAB](./matlab.md)
- [Julia](./julia.md)
- [SAS](./sas.md)
- [Stata](./stata.md)
- [Wolfram Language](./wolfram-language.md)
- [Fortran](./fortran.md)
- [Assembly](./assembly.md)
- [Zig](./zig.md)
- [Ada](./ada.md)
- [COBOL](./cobol.md)
- [Delphi/Object Pascal](./delphi-object-pascal.md)
- [ABAP](./abap.md)
- [PL/SQL](./pl-sql.md)
- [T-SQL](./t-sql.md)
- [Haskell](./haskell.md)
- [OCaml](./ocaml.md)
- [F#](./fsharp.md)
- [Erlang](./erlang.md)
- [Elixir](./elixir.md)
- [Lisp/Common Lisp](./lisp-common-lisp.md)
- [Clojure](./clojure.md)
- [Prolog](./prolog.md)
- [GDScript](./gdscript.md)
- [HLSL](./hlsl.md)
- [GLSL](./glsl.md)
- [CUDA C/C++](./cuda-c-cplusplus.md)
- [OpenCL C](./opencl-c.md)
- [VHDL](./vhdl.md)
- [Verilog/SystemVerilog](./verilog-systemverilog.md)
- [HCL](./hcl.md)
- [YAML](./yaml.md)
- [JSONnet](./jsonnet.md)
- [Solidity](./solidity.md)
- [Move](./move.md)
- [Apex](./apex.md)
- [Hack](./hack.md)
- [Nim](./nim.md)
- [Crystal](./crystal.md)
- [D](./d.md)
- [Forth](./forth.md)
- [Tcl](./tcl.md)
- [AWK](./awk.md)
- [AutoHotkey](./autohotkey.md)
- [Mojo](./mojo.md)
- [Carbon](./carbon.md)
- [WAT](./wat.md)
- [Smalltalk](./smalltalk.md)
- [Racket](./racket.md)
- [Gleam](./gleam.md)
- [Lean](./lean.md)

## 참고 출처

- [TIOBE Index](https://www.tiobe.com/tiobe-index/)
- [Stack Overflow Developer Survey 2025](https://survey.stackoverflow.co/2025/technology)
- [GitHub Octoverse 2025](https://github.blog/news-insights/octoverse/octoverse-a-new-developer-joins-github-every-second-as-ai-leads-typescript-to-1/)

---

## 프로그래밍 언어 reference

75개 프로그래밍 언어의 사용처/특징/장점/제약/실사용 예제/관련 문서/분야별 진입점. 자세한 내용은 `references/languages/` 디렉토리 참조.

- 메인 인덱스 + 우선순위 표: [./index.md](./index.md)
- 분야별 진입점 (웹/AI/모바일/게임/시스템/DevOps 등): [./domains.md](./domains.md)
- 언어별 상세: [./<lang>.md](./)

## /language <id> 호출 동작

1. 사용자가 `/language <id>` 또는 자연어 ("Python 언어 정리", "Kotlin 비교") 호출.
2. ID resolve: SKILL.md `### 언어 별칭` 표에서 별칭이면 primary ID 로 치환.
3. `references/languages/<id>.md` 본문 로드 — 핵심 판단 / 사용처 / 특징 / 장점 / 제약 / 적합 프로젝트 / 생태계 / 학습 난이도 / 운영-배포 / 타입-런타임 / 실사용 예제 / 관련 문서 / 비교 포인트 / 도입 전 체크리스트 / 최신 확인 항목.
4. 분야별 추천 또는 비교 요청이면 `references/languages/domains.md` 와 `index.md` 의 우선순위 표를 함께 활용.
5. 최신 순위·점유율·채용·연봉·릴리스 상태 같이 변동 정보는 답변 전 웹으로 별도 확인.

## 언어 ID 명명 규칙

- 영문명을 kebab-case 변환 후 lowercase.
- 특수 기호는 ASCII 정규화: `C#` → `csharp`, `C++` → `cplusplus`, `F#` → `fsharp`, `T-SQL` → `t-sql`, `PL/SQL` → `pl-sql`, `Objective-C` → `objective-c`, `Visual Basic .NET` → `visual-basic-dotnet`.
- `JavaScript` → `javascript`, `TypeScript` → `typescript`.

### 언어 별칭

| 별칭 | Primary ID |
|------|-----------|
| js | javascript |
| ts | typescript |
| py | python |
| c++ | cplusplus |
| c# | csharp |
| f# | fsharp |
| objc | objective-c |
| vb | visual-basic-dotnet |
| vb.net | visual-basic-dotnet |
| ps | powershell |
| sh | bash-shell |
| shell | bash-shell |

## 언어 자동 감지

프로젝트 구조를 분석하여 적합한 언어를 자동 선택합니다 (75 언어 카탈로그와 1:1 매핑).

| 파일/디렉토리 | 감지 언어 | `/language <id>` lookup |
|--------------|----------|------------------------|
| `*.kt`, `*.kts`, `build.gradle.kts`           | Kotlin     | `/language kotlin` |
| `*.java`, `pom.xml`, `build.gradle`           | Java       | `/language java` |
| `*.swift`, `Package.swift`, `*.xcodeproj/`    | Swift      | `/language swift` |
| `*.py`, `requirements.txt`, `pyproject.toml`, `setup.py` | Python | `/language python` |
| `*.js`, `*.mjs`, `*.cjs`, `package.json`      | JavaScript | `/language javascript` |
| `*.ts`, `*.tsx`, `tsconfig.json`              | TypeScript | `/language typescript` |
| `*.go`, `go.mod`, `go.sum`                    | Go         | `/language go` |
| `*.rs`, `Cargo.toml`, `Cargo.lock`            | Rust       | `/language rust` |
| `*.cpp`, `*.cc`, `*.cxx`, `*.hpp`, `CMakeLists.txt` | C++  | `/language cplusplus` |
| `*.cs`, `*.csproj`, `*.sln`                   | C#         | `/language csharp` |
| `*.rb`, `Gemfile`, `Rakefile`                 | Ruby       | `/language ruby` |
| `*.php`, `composer.json`, `composer.lock`     | PHP        | `/language php` |
| `*.scala`, `*.sbt`, `build.sbt`               | Scala      | `/language scala` |

다중 언어 프로젝트는 우선순위 — 빌드 매니페스트(go.mod / Cargo.toml / package.json / pom.xml 등) > 소스 파일 수 > 사용자 명시. 위 13 언어 외 추가 감지가 필요하면 `./index.md` 의 75 언어 진입점 + 별칭 표 참조.
