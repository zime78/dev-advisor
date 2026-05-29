<!-- markdownlint-disable MD013 -->

# C\#

원천: `docs/PROGRAMMING_LANGUAGES_2026.md`, 기준일 2026-05-13. 최신 순위와 시장 지표는 답변 시점에 웹으로 확인한다.

## 핵심 판단

.NET 백엔드, Windows, Unity, 기업 시스템을 함께 고려하면 강한 생산성을 제공한다. C\# 도입 판단은 문법 선호보다 실행 환경, 기존 자산, 운영 인력의 숙련도에 더 크게 좌우된다. 제품의 주 경로가 .NET 백엔드, Windows 앱, Unity 게임, 기업 시스템이고, 다음 제약을 통제할 수 있다면 우선 검토할 만하다: 일부 조직에서는 Windows/.NET 중심 인프라에 묶이는 느낌을 받을 수 있다.

## 사용처

.NET 백엔드, Windows 앱, Unity 게임, 기업 시스템. 실무에서는 이 범위를 넘어 모든 문제를 해결하는 범용 선택지로 보기보다, C\# 생태계가 이미 강한 플랫폼과 도구 체인에 맞춰 채택하는 편이 안정적이다. 신규 프로젝트에서는 장기 유지보수 인력과 배포 대상의 제약을 함께 확인해야 한다.

## 특징

Microsoft 생태계의 정적 타입 언어. 코드 작성 모델, 빌드 방식, 런타임 제약이 프로젝트 구조에 직접 영향을 주므로 초기 설계 단계에서 테스트 전략과 패키지 관리 방식을 같이 정해야 한다.

## 장점

언어 기능이 현대적이고, ASP.NET Core와 Unity 생태계가 강하다. 특히 기존 생태계의 표준 도구를 그대로 활용할 수 있을 때 생산성과 운영 예측 가능성이 높다. 팀이 관용구와 디버깅 방식을 익히면 같은 기능을 더 적은 접착 코드로 구현할 수 있다.

## 제약

일부 조직에서는 Windows/.NET 중심 인프라에 묶이는 느낌을 받을 수 있다. 이 제약은 작은 실험에서는 드러나지 않다가 배포, 성능, 보안 감사, 장기 유지보수 단계에서 비용으로 나타나는 경우가 많다. 도입 전에는 대체 언어와 운영 모델을 같이 비교해야 한다.

## 적합한 프로젝트

- ASP.NET Core API, Windows 앱, Unity 게임, Microsoft/Azure 중심 기업 시스템.
- 언어 기능과 IDE, 런타임, 프레임워크 통합도가 중요한 팀.
- C\# 표준 도구와 런타임을 팀이 직접 운영할 수 있고, 코드 리뷰에서 언어별 관용구를 일관되게 적용할 수 있는 프로젝트.

## 부적합하거나 주의할 프로젝트

- Microsoft/.NET 생태계 의존을 피해야 하는 조직.
- Unity와 서버 .NET의 런타임 차이를 혼동하는 프로젝트.
- C\# 경험자가 없는데 핵심 장애 대응, 성능 튜닝, 릴리스 자동화까지 동시에 요구되는 프로젝트.

## 대표 생태계와 도구

- .NET SDK, CLR
- NuGet, MSBuild
- xUnit, NUnit, MSTest
- ASP.NET Core, Entity Framework Core, Unity

## 학습 난이도와 선행 지식

객체지향, LINQ, async/await, nullable reference type, .NET 프로젝트 구조를 함께 익혀야 한다. 입문 단계에서는 문법보다 작은 프로그램을 빌드, 테스트, 포맷, 배포하는 전체 흐름을 먼저 익히는 것이 좋다. 실무 투입 전에는 오류 처리, 의존성 관리, 표준 라이브러리 사용법을 팀 규칙으로 정리해야 한다.

## 운영/배포 관점

단일 파일/컨테이너 배포가 가능하지만 런타임 버전, 트리밍, 설정, 관측 표준을 맞춰야 한다. 재현 가능한 빌드, 의존성 잠금, 런타임 버전 고정, 관측 로그 포맷을 초기에 정하지 않으면 운영 환경 차이로 인한 결함이 늘어난다.

## 타입/런타임 특성

정적 타입, GC, async/await, 풍부한 런타임 메타데이터를 제공한다. 이 특성은 API 경계, 테스트 범위, 병렬성 모델, 장애 격리 방식에 영향을 준다. 언어의 타입 시스템이 보장하지 않는 부분은 정적 분석, 테스트, 코드 리뷰 규칙으로 보완해야 한다.

## 실사용 예제

다음 예제는 이 언어를 단순 출력이 아니라 실제 업무 코드에서 자주 나오는 데이터 집계, 자동화, 런타임 제어, 또는 플랫폼 특화 작업에 적용하는 형태로 보여준다.

```csharp
using System;
using System.Collections.Generic;
using System.Linq;

record Order(string Region, decimal Amount, bool Paid);

var orders = new List<Order> {
    new("apac", 120_000m, true),
    new("emea", 90_000m, true),
    new("apac", 30_000m, false)
};

var report = orders
    .Where(order => order.Paid)
    .GroupBy(order => order.Region)
    .Select(group => new { Region = group.Key, Revenue = group.Sum(x => x.Amount) });

foreach (var row in report)
    Console.WriteLine($"{row.Region}: {row.Revenue:N0}");
```

## 관련 문서

- [C# Documentation](https://learn.microsoft.com/dotnet/csharp/)
- [C# Language Reference](https://learn.microsoft.com/dotnet/csharp/language-reference/)
- [.NET CLI](https://learn.microsoft.com/dotnet/core/tools/)

## 비교 포인트

- [Python](./python.md): 생태계와 채용 풀, 장기 유지보수성, 배포 환경 제약을 우선 비교한다.
- [JavaScript](./javascript.md): 성능보다 생산성이 중요한지, 컴파일 시점 보장이 중요한지, 런타임 유연성이 중요한지 구분한다.
- [SQL](./sql.md): 표준 라이브러리와 패키지 관리가 팀의 보안·라이선스 정책에 맞는지 확인한다.
- [TypeScript](./typescript.md): 기존 코드베이스와의 상호 운용, 마이그레이션 비용, 관측/디버깅 도구 성숙도를 함께 본다.
- [Java](./java.md): 생태계와 채용 풀, 장기 유지보수성, 배포 환경 제약을 우선 비교한다.
- [Go](./go.md): 성능보다 생산성이 중요한지, 컴파일 시점 보장이 중요한지, 런타임 유연성이 중요한지 구분한다.

## 함께 비교할 언어

- [Python](./python.md)
- [JavaScript](./javascript.md)
- [SQL](./sql.md)
- [TypeScript](./typescript.md)
- [Java](./java.md)
- [Go](./go.md)

## 추천 학습/도입 상황

- 제품의 핵심 경로가 .NET 백엔드, Windows 앱, Unity 게임, 기업 시스템이고, 팀이 C\#의 표준 빌드·테스트·배포 흐름을 문서화할 수 있을 때 도입 우선순위를 높인다.
- 다음 강점이 일정, 품질, 운영 비용 중 하나를 명확히 낮출 때 실무 채택 근거가 충분하다: 언어 기능이 현대적이고, ASP.NET Core와 Unity 생태계가 강하다.
- 다음 제약이 핵심 리스크라면 파일럿 구현, 성능 측정, 장애 대응 연습을 거친 뒤 본격 도입한다: 일부 조직에서는 Windows/.NET 중심 인프라에 묶이는 느낌을 받을 수 있다.

## 도입 전 체크리스트

- 현재 팀이 이 언어의 빌드, 테스트, 디버깅, 배포 흐름을 문서화하고 반복 실행할 수 있는지 확인한다.
- 핵심 라이브러리와 프레임워크의 유지보수 상태, 라이선스, 보안 업데이트 흐름을 확인한다.
- 대체 언어와 비교해 학습 비용, 운영 리스크, 장기 인력 수급이 프로젝트 기간에 맞는지 확인한다.
- 공식 문서, 언어 스펙 또는 레퍼런스, 패키지/툴링 문서를 최소 1회 확인하고 프로젝트 표준 링크로 남긴다.

## 최신 확인 필요

- 인기 순위, 점유율, 채용 수요, 연봉 데이터는 답변 시점의 최신 자료로 확인한다.
- 최신 안정 버전, LTS 정책, 주요 프레임워크 버전은 공식 문서나 릴리스 노트로 확인한다.
- 보안 권고, 패키지 생태계 상태, 플랫폼 지원 종료 여부는 프로젝트 도입 전에 별도 확인한다.
