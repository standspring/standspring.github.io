---
title: "Unity Build란? 탄생 배경부터 장단점, CMake 적용 방법까지"
description: "C/C++ 빌드 최적화 기법인 Unity Build의 개념, 탄생 배경, 동작 원리, 장점과 단점, 적용 기준, CMake 예제, 실무 체크리스트를 정리합니다."
date: 2026-05-20
categories: [C++, Build]
tags: [unity-build, jumbo-build, cpp, cplusplus, cmake, compile-time, build-optimization]
---

![Unity Build 개념도](/assets/img/2026-05-20-unity-build.svg)

`Unity Build`는 여러 개의 C/C++ 소스 파일을 하나의 큰 소스 파일처럼 묶어서 컴파일하는 빌드 방식입니다.
다른 이름으로는 `Jumbo Build`, `Bulk Build`, `Single Compilation Unit Build`라고도 부릅니다.

이름 때문에 Unity 게임 엔진의 빌드 기능으로 오해하기 쉽지만, 여기서 말하는 Unity Build는 **C/C++ 컴파일 시간을 줄이기 위한 빌드 최적화 기법**입니다.

예를 들어 원래는 아래처럼 각각 컴파일하던 파일들이 있습니다.

```text
a.cpp -> a.o
b.cpp -> b.o
c.cpp -> c.o
```

Unity Build에서는 임시 파일을 하나 만들고, 그 안에서 여러 `.cpp` 파일을 `#include`합니다.

```cpp
// unity_0.cpp
#include "a.cpp"
#include "b.cpp"
#include "c.cpp"
```

그리고 컴파일러는 `unity_0.cpp` 하나를 하나의 translation unit으로 컴파일합니다.

```text
unity_0.cpp -> unity_0.o
```

핵심은 간단합니다.

> 컴파일러가 반복해서 처리하던 공통 헤더, 템플릿, 전처리 작업을 한 번에 묶어 처리해서 전체 빌드 시간을 줄이는 방식입니다.

---

## 1. Unity Build가 탄생한 배경

C와 C++의 빌드 모델은 오래된 구조를 기반으로 합니다.
각 `.cpp` 파일은 독립적인 `translation unit`으로 컴파일되고, 마지막에 링커가 여러 object file을 합쳐 실행 파일이나 라이브러리를 만듭니다.

```text
전처리 -> 컴파일 -> 어셈블 -> 링크
```

문제는 프로젝트가 커질수록 같은 헤더를 너무 많이 반복해서 읽는다는 점입니다.

예를 들어 `a.cpp`, `b.cpp`, `c.cpp`가 모두 아래 헤더들을 포함한다고 가정해보겠습니다.

```cpp
#include <vector>
#include <string>
#include <map>
#include "Common.h"
#include "Logger.h"
#include "Config.h"
```

일반 빌드에서는 세 소스 파일을 각각 컴파일하므로, 컴파일러는 비슷한 헤더 트리를 세 번 처리합니다.

```text
a.cpp 컴파일: vector, string, map, Common.h, Logger.h, Config.h 처리
b.cpp 컴파일: vector, string, map, Common.h, Logger.h, Config.h 처리
c.cpp 컴파일: vector, string, map, Common.h, Logger.h, Config.h 처리
```

소스 파일이 10개일 때는 큰 문제가 아닐 수 있습니다.
하지만 소스 파일이 수백 개, 수천 개가 되고 템플릿과 매크로가 많은 C++ 프로젝트가 되면 이야기가 달라집니다.

특히 C++은 아래 요소 때문에 컴파일 시간이 쉽게 커집니다.

- 표준 라이브러리 헤더가 크다.
- 템플릿 인스턴스화 비용이 크다.
- 헤더 파일에 구현이 들어가는 경우가 많다.
- 전처리기가 include 트리를 매번 펼친다.
- 매크로와 조건부 컴파일이 많으면 파싱 비용이 늘어난다.
- 각 translation unit마다 컴파일러 초기화와 최적화 비용이 반복된다.

그래서 대형 C++ 프로젝트에서는 전체 빌드 시간이 개발 생산성의 병목이 됩니다.

```text
코드 수정 1분
빌드 대기 10분
테스트 실행 5분
다시 수정
다시 대기
```

이런 흐름이 반복되면 개발자는 작은 수정도 부담스럽게 느끼게 됩니다.
Unity Build는 이 문제를 완화하기 위해 등장한 실용적인 해결책입니다.

---

## 2. 일반 빌드와 Unity Build 비교

일반 빌드는 `.cpp` 파일 하나가 object file 하나로 이어지는 구조입니다.

```text
a.cpp -> a.o
b.cpp -> b.o
c.cpp -> c.o
d.cpp -> d.o
```

Unity Build는 여러 `.cpp` 파일을 묶은 임시 파일을 컴파일합니다.

```text
unity_0.cpp
  ├─ #include "a.cpp"
  ├─ #include "b.cpp"
  └─ #include "c.cpp"

unity_1.cpp
  ├─ #include "d.cpp"
  ├─ #include "e.cpp"
  └─ #include "f.cpp"
```

결과적으로 object file 수도 줄어듭니다.

```text
일반 빌드: a.o, b.o, c.o, d.o, e.o, f.o
Unity Build: unity_0.o, unity_1.o
```

빌드 시스템이 Unity Build를 지원하는 경우, 개발자가 직접 `unity_0.cpp`를 작성하지 않아도 됩니다.
CMake, Unreal Build Tool, Chromium의 Jumbo Build 같은 시스템은 내부적으로 이런 파일을 생성하거나 유사한 방식으로 묶어줍니다.

---

## 3. 왜 빨라지는가?

Unity Build가 빨라지는 이유는 단순히 "파일 수가 줄어서"만은 아닙니다.
실제로는 여러 비용이 함께 줄어듭니다.

### 3-1. 헤더 파싱 반복 감소

C++ 컴파일 시간의 큰 부분은 헤더를 읽고 파싱하는 데 사용됩니다.
같은 헤더가 여러 `.cpp`에서 반복적으로 include되면 컴파일러는 그 작업을 반복합니다.

Unity Build에서는 여러 `.cpp`가 하나의 translation unit 안에 들어가므로 공통 헤더 처리 비용이 줄어들 수 있습니다.

물론 include guard나 `#pragma once`가 있어도 일반 빌드에서는 translation unit마다 다시 처리합니다.
include guard는 한 translation unit 안에서 중복 include를 막아줄 뿐, 여러 `.cpp` 파일 사이의 반복 파싱을 완전히 없애지는 못합니다.

### 3-2. 컴파일러 프로세스 시작 비용 감소

소스 파일이 많으면 컴파일러 실행도 많아집니다.
각 실행에는 프로세스 시작, 옵션 처리, 파일 열기, 전처리 환경 구성 같은 비용이 있습니다.

Unity Build는 컴파일 단위 수를 줄이므로 이런 고정 비용도 줄어듭니다.

### 3-3. 템플릿과 인라인 코드 처리 효율 증가

C++ 프로젝트는 템플릿과 인라인 함수가 많습니다.
일반 빌드에서는 비슷한 템플릿 코드가 여러 translation unit에서 반복 처리될 수 있습니다.

Unity Build에서는 같은 translation unit 안에서 처리되는 코드 범위가 커지므로 일부 반복 비용이 줄어들 수 있습니다.

### 3-4. 링크할 object file 수 감소

object file 수가 줄면 링크 단계의 입력 파일 수도 줄어듭니다.
프로젝트에 따라 링크 시간도 어느 정도 줄어들 수 있습니다.

다만 링크 시간 개선은 프로젝트 구조, 링커, LTO 사용 여부에 따라 다릅니다.
Unity Build의 가장 큰 효과는 보통 컴파일 단계에서 나타납니다.

---

## 4. 간단한 예제

아래와 같은 프로젝트가 있다고 가정해보겠습니다.

```text
src/
  main.cpp
  math.cpp
  string_util.cpp
  file_util.cpp
include/
  math.h
  string_util.h
  file_util.h
```

일반 빌드에서는 아래처럼 각각 컴파일합니다.

```bash
g++ -c src/main.cpp -o main.o
g++ -c src/math.cpp -o math.o
g++ -c src/string_util.cpp -o string_util.o
g++ -c src/file_util.cpp -o file_util.o
g++ main.o math.o string_util.o file_util.o -o app
```

Unity Build에서는 이런 파일을 만들 수 있습니다.

```cpp
// unity.cpp
#include "src/main.cpp"
#include "src/math.cpp"
#include "src/string_util.cpp"
#include "src/file_util.cpp"
```

그리고 하나의 파일처럼 컴파일합니다.

```bash
g++ -c unity.cpp -o unity.o
g++ unity.o -o app
```

실무에서는 직접 이렇게 구성하기보다 빌드 시스템에 맡기는 편이 좋습니다.
직접 작성하면 파일 추가와 제외, 플랫폼별 조건, 디버깅 설정을 관리하기 어려워집니다.

---

## 5. CMake에서 Unity Build 사용하기

CMake는 `UNITY_BUILD` 속성을 지원합니다.
대상 타겟에 아래처럼 설정할 수 있습니다.

```cmake
cmake_minimum_required(VERSION 3.16)
project(UnityBuildExample LANGUAGES CXX)

add_executable(my_app
    src/main.cpp
    src/math.cpp
    src/string_util.cpp
    src/file_util.cpp
)

set_target_properties(my_app PROPERTIES
    CXX_STANDARD 17
    CXX_STANDARD_REQUIRED ON
    UNITY_BUILD ON
)
```

전체 프로젝트에 기본값으로 켜고 싶다면 아래처럼 설정할 수도 있습니다.

```cmake
set(CMAKE_UNITY_BUILD ON)
```

하지만 처음부터 전체 프로젝트에 켜는 것은 추천하지 않습니다.
먼저 특정 라이브러리나 실행 파일 하나에만 적용해보고, 문제가 없는지 확인하는 방식이 좋습니다.

### 묶음 크기 조절

CMake에서는 한 unity source에 몇 개의 원본 파일을 묶을지 조절할 수 있습니다.

```cmake
set_target_properties(my_app PROPERTIES
    UNITY_BUILD ON
    UNITY_BUILD_BATCH_SIZE 8
)
```

`BATCH_SIZE`가 너무 크면 한 파일 수정 시 다시 컴파일해야 하는 범위가 커집니다.
반대로 너무 작으면 Unity Build의 효과가 줄어듭니다.

처음에는 `4`, `8`, `16` 정도를 비교해보는 것이 좋습니다.

### 특정 파일 제외

Unity Build에 포함되면 문제가 생기는 파일은 제외할 수 있습니다.

```cmake
set_source_files_properties(src/special_case.cpp PROPERTIES
    SKIP_UNITY_BUILD_INCLUSION ON
)
```

매크로 충돌, 전역 변수 충돌, 플랫폼별 조건이 복잡한 파일은 이렇게 제외하는 편이 안전합니다.

---

## 6. Unity Build의 장점

### 6-1. 전체 빌드 시간이 줄어든다

가장 큰 장점은 전체 빌드 속도입니다.
대형 C++ 프로젝트에서는 Unity Build를 켰을 때 전체 빌드 시간이 크게 줄어드는 경우가 많습니다.

특히 아래 조건에 해당하면 효과가 잘 나옵니다.

- `.cpp` 파일이 많다.
- 공통 헤더가 매우 크다.
- 템플릿 라이브러리를 많이 쓴다.
- 헤더 include 트리가 깊다.
- 클린 빌드 시간이 길다.
- CI에서 매번 전체 빌드에 가까운 작업을 수행한다.

### 6-2. CI 비용을 줄일 수 있다

CI 서버에서 C++ 프로젝트를 자주 빌드하면 시간이 곧 비용입니다.
빌드 시간이 30분에서 15분으로 줄어들면 개발자 피드백도 빨라지고, CI 자원도 절약됩니다.

PR 검증 시간이 줄면 코드 리뷰 흐름도 좋아집니다.

```text
PR 생성
-> 빌드 대기
-> 테스트 대기
-> 리뷰
-> 수정
-> 재검증
```

이 사이클이 짧아질수록 팀 전체의 개발 속도가 올라갑니다.

### 6-3. 컴파일러 최적화 기회가 늘어날 수 있다

여러 소스 파일이 하나의 translation unit이 되면 컴파일러가 더 넓은 범위의 코드를 한 번에 볼 수 있습니다.
그 결과 일부 함수 인라이닝이나 dead code 제거가 더 잘 될 수 있습니다.

다만 이 효과는 항상 보장되지 않습니다.
현대 빌드에서는 LTO(Link Time Optimization)를 쓰는 경우도 많기 때문에, Unity Build를 성능 최적화 수단으로만 보는 것은 조심해야 합니다.

Unity Build의 주목적은 보통 실행 성능보다 **빌드 시간 단축**입니다.

### 6-4. 숨은 include 누락을 발견할 수 있다

의외의 장점도 있습니다.
Unity Build를 켜면 파일 간 include 순서가 바뀌면서 어떤 파일이 자기에게 필요한 헤더를 직접 include하지 않았다는 사실이 드러날 수 있습니다.

예를 들어 `foo.cpp`가 우연히 `bar.cpp`가 먼저 include한 헤더에 의존하고 있었다면, Unity Build 구성 순서가 바뀌는 순간 컴파일 오류가 날 수 있습니다.

이것은 귀찮은 오류처럼 보이지만, 사실은 코드의 독립성이 깨져 있었다는 신호입니다.

---

## 7. Unity Build의 단점

Unity Build는 강력하지만 공짜는 아닙니다.
특히 C++의 복잡한 이름 규칙, 전처리기, 전역 심볼, 익명 namespace와 만나면 예상하지 못한 문제가 생길 수 있습니다.

### 7-1. 증분 빌드가 느려질 수 있다

Unity Build는 여러 `.cpp`를 하나로 묶습니다.
따라서 그 안에 포함된 파일 하나만 수정해도 묶음 전체를 다시 컴파일해야 합니다.

예를 들어 `unity_0.cpp`가 아래 파일을 포함한다고 해보겠습니다.

```cpp
#include "a.cpp"
#include "b.cpp"
#include "c.cpp"
#include "d.cpp"
#include "e.cpp"
```

이때 `c.cpp` 한 줄만 수정해도 `a.cpp`부터 `e.cpp`까지 들어있는 unity translation unit이 다시 컴파일됩니다.

그래서 Unity Build는 보통 클린 빌드나 CI 빌드에는 유리하지만, 로컬에서 자주 한 파일씩 고치는 개발 흐름에서는 오히려 불리할 수 있습니다.

### 7-2. 파일 간 매크로 오염이 발생할 수 있다

Unity Build에서는 여러 `.cpp` 파일이 같은 translation unit 안에 들어갑니다.
그러면 한 파일에서 정의한 매크로가 뒤에 include되는 파일에 영향을 줄 수 있습니다.

```cpp
// a.cpp
#define private public
#include "SomeClass.h"
```

```cpp
// b.cpp
#include "OtherClass.h"
```

일반 빌드에서는 `a.cpp`의 매크로가 `b.cpp`에 영향을 주지 않습니다.
하지만 Unity Build에서 `a.cpp` 뒤에 `b.cpp`가 포함되면 `private` 매크로가 살아 있는 상태로 `b.cpp`를 오염시킬 수 있습니다.

이런 코드는 반드시 정리해야 합니다.

```cpp
#define private public
#include "SomeClass.h"
#undef private
```

### 7-3. 익명 namespace와 static 심볼 충돌이 생길 수 있다

일반 빌드에서는 각 `.cpp` 파일이 서로 다른 translation unit입니다.
그래서 각 파일에 같은 이름의 `static` 함수나 익명 namespace 내부 함수가 있어도 충돌하지 않습니다.

```cpp
// a.cpp
namespace {
int helper() { return 1; }
}
```

```cpp
// b.cpp
namespace {
int helper() { return 2; }
}
```

일반 빌드에서는 문제가 없습니다.
하지만 Unity Build에서는 두 파일이 같은 translation unit에 들어오므로 재정의 오류가 발생할 수 있습니다.

해결 방법은 이름을 더 구체적으로 바꾸거나, 문제가 되는 파일을 Unity Build에서 제외하는 것입니다.

### 7-4. ODR 문제가 가려지거나 새로 드러날 수 있다

C++에는 ODR(One Definition Rule)이 있습니다.
간단히 말하면 프로그램 안에서 어떤 엔티티는 정의가 하나여야 한다는 규칙입니다.

Unity Build는 translation unit 경계를 바꾸기 때문에 ODR 문제가 다르게 드러날 수 있습니다.
일반 빌드에서는 링크 단계에서 나오던 오류가 컴파일 단계에서 나올 수도 있고, 반대로 특정 문제가 우연히 가려질 수도 있습니다.

그래서 Unity Build만 통과한다고 코드가 항상 건강하다고 볼 수는 없습니다.
가능하면 일반 빌드도 CI에서 함께 돌리는 것이 좋습니다.

### 7-5. include 의존성이 흐려질 수 있다

Unity Build에서는 앞에 포함된 `.cpp`가 어떤 헤더를 이미 include했기 때문에 뒤 파일이 우연히 컴파일되는 경우가 있습니다.

```cpp
// a.cpp
#include <vector>
```

```cpp
// b.cpp
std::vector<int> values;
```

`b.cpp`가 `<vector>`를 직접 include하지 않았는데도 Unity Build에서는 통과할 수 있습니다.
하지만 일반 빌드로 돌아가면 깨집니다.

좋은 C++ 코드는 각 파일이 자신에게 필요한 헤더를 직접 include해야 합니다.

> "내가 쓰는 것은 내가 include한다"는 원칙이 중요합니다.

### 7-6. 디버깅과 경고 위치가 헷갈릴 수 있다

Unity Build에서는 컴파일러가 생성된 `unity_0.cpp`를 기준으로 오류를 보고할 수 있습니다.
도구가 잘 지원하면 원본 파일 위치를 보여주지만, 환경에 따라 경고 위치가 헷갈릴 수 있습니다.

또한 하나의 큰 파일처럼 컴파일되기 때문에 경고가 한꺼번에 많이 쏟아질 수 있습니다.

### 7-7. 병렬 빌드 효율이 떨어질 수 있다

일반 빌드에서는 `.cpp` 파일이 많으므로 빌드 시스템이 여러 CPU 코어에 작업을 잘 분배할 수 있습니다.

```text
16개 코어 -> 16개 .cpp 동시 컴파일
```

Unity Build에서 파일을 너무 크게 묶으면 컴파일 단위 수가 줄어듭니다.
그러면 병렬로 처리할 작업이 부족해질 수 있습니다.

```text
16개 코어 -> unity_0.cpp, unity_1.cpp만 컴파일
```

따라서 Unity Build는 무조건 크게 묶는 것이 답이 아닙니다.
빌드 서버의 CPU 코어 수, 소스 파일 수, 파일별 컴파일 시간을 고려해서 묶음 크기를 조절해야 합니다.

---

## 8. Unity Build가 잘 맞는 프로젝트

Unity Build는 아래 프로젝트에 잘 맞습니다.

- C++ 소스 파일 수가 많다.
- 클린 빌드 시간이 길다.
- CI에서 전체 빌드가 자주 돈다.
- 공통 헤더가 크고 include 트리가 복잡하다.
- 소스 파일 간 전역 매크로 사용이 적다.
- 파일별 독립성이 비교적 잘 지켜져 있다.
- 빌드 시간을 줄이는 것이 팀 생산성에 큰 영향을 준다.

특히 게임 엔진, 브라우저, 대형 데스크톱 애플리케이션, 시뮬레이션 프로그램, 임베디드 SDK, 대형 라이브러리에서 검토할 만합니다.

---

## 9. Unity Build가 잘 안 맞는 프로젝트

반대로 아래 상황에서는 신중해야 합니다.

- 소스 파일마다 매크로 상태가 복잡하게 다르다.
- `static` 함수나 익명 namespace에 같은 이름이 많다.
- 오래된 C 코드처럼 전역 변수와 전역 매크로가 많다.
- 한 파일만 자주 수정하는 로컬 개발이 대부분이다.
- 일반 빌드도 이미 충분히 빠르다.
- 빌드 오류 분석과 디버깅 도구가 Unity Build를 잘 지원하지 않는다.
- 코드 품질이 낮아 파일 간 숨은 의존성이 많다.

이런 프로젝트에 무리하게 Unity Build를 켜면 빌드 속도는 조금 좋아져도 유지보수 비용이 더 커질 수 있습니다.

---

## 10. Unity Build와 Precompiled Header 비교

Unity Build와 PCH(Precompiled Header)는 모두 빌드 시간을 줄이는 방법이지만 접근 방식이 다릅니다.

| 구분 | Unity Build | Precompiled Header |
|---|---|---|
| 핵심 아이디어 | 여러 `.cpp`를 하나로 묶음 | 자주 쓰는 헤더를 미리 컴파일 |
| 주 효과 | translation unit 수 감소 | 헤더 파싱 비용 감소 |
| 장점 | 설정이 비교적 단순, 효과가 큰 경우 많음 | 소스 파일 경계를 유지 |
| 단점 | 매크로 오염, 심볼 충돌, 증분 빌드 악화 가능 | PCH 구성 관리 필요 |
| 추천 사용 | 클린 빌드/CI 최적화 | 로컬 개발과 전체 빌드 모두에 유용 |

둘은 경쟁 관계라기보다 함께 쓸 수 있는 도구입니다.
대형 프로젝트에서는 PCH, ccache/sccache, Ninja, 병렬 빌드, Unity Build를 조합해서 사용합니다.

---

## 11. Unity Build와 LTO 비교

LTO(Link Time Optimization)는 링크 단계에서 여러 object file을 함께 분석해 최적화하는 기법입니다.

Unity Build와 LTO는 목적이 다릅니다.

| 구분 | Unity Build | LTO |
|---|---|---|
| 주 목적 | 빌드 시간 단축 | 실행 파일 최적화 |
| 적용 단계 | 컴파일 단계 | 링크 단계 |
| 코드 경계 | 여러 `.cpp`를 한 translation unit으로 묶음 | object file 경계를 넘어 최적화 |
| 빌드 시간 영향 | 보통 단축 | 보통 증가 가능 |
| 산출물 성능 | 일부 개선 가능 | 성능/크기 개선 가능 |

실행 성능 최적화가 목적이면 LTO를 검토하고, 빌드 대기 시간이 문제라면 Unity Build를 검토하는 식으로 구분하면 됩니다.

---

## 12. 실무 적용 전략

Unity Build는 한 번에 전체 프로젝트에 켜기보다 단계적으로 적용하는 것이 좋습니다.

### 12-1. 현재 빌드 시간을 먼저 측정한다

최적화는 측정부터 시작해야 합니다.

```text
일반 클린 빌드 시간
일반 증분 빌드 시간
Unity Build 클린 빌드 시간
Unity Build 증분 빌드 시간
CI 빌드 시간
로컬 빌드 시간
```

측정 없이 "빨라질 것이다"라고 가정하면 잘못된 결정을 하기 쉽습니다.

### 12-2. 작은 타겟부터 켠다

처음에는 전체 프로젝트가 아니라 특정 라이브러리 하나에만 적용합니다.

```cmake
set_target_properties(core_lib PROPERTIES UNITY_BUILD ON)
```

문제가 없다면 다른 타겟으로 넓혀갑니다.

### 12-3. 문제 파일은 제외한다

Unity Build에서 자주 문제를 일으키는 파일은 과감히 제외하는 것이 좋습니다.

```cmake
set_source_files_properties(src/legacy_macro_heavy.cpp PROPERTIES
    SKIP_UNITY_BUILD_INCLUSION ON
)
```

빌드 속도 100% 최적화보다 안정적으로 유지되는 80% 최적화가 더 낫습니다.

### 12-4. 일반 빌드도 유지한다

Unity Build만 CI에서 돌리면 include 누락 같은 문제가 가려질 수 있습니다.
따라서 가능하면 일반 빌드도 별도 job으로 유지하는 것이 좋습니다.

추천 구성은 아래와 같습니다.

```text
PR 빠른 검증: Unity Build ON
야간 빌드: Unity Build OFF + 전체 테스트
릴리즈 빌드: 프로젝트 정책에 따라 ON/OFF 고정
```

### 12-5. 코드 규칙을 같이 정리한다

Unity Build를 안정적으로 쓰려면 코드 규칙도 중요합니다.

- `.cpp`는 자신이 쓰는 헤더를 직접 include한다.
- 매크로를 정의했다면 가능한 한 빨리 `#undef`한다.
- 전역 변수와 전역 상태를 줄인다.
- 익명 namespace 내부 이름도 너무 일반적으로 짓지 않는다.
- 파일 include 순서에 의존하지 않는다.
- generated file, platform-specific file, legacy file은 별도 관리한다.

---

## 13. 자주 만나는 오류와 해결 방법

### 같은 이름의 함수가 재정의된다는 오류

원인:

```cpp
// a.cpp
namespace {
void Init() {}
}
```

```cpp
// b.cpp
namespace {
void Init() {}
}
```

해결:

- 함수 이름을 더 구체적으로 변경한다.
- 클래스로 캡슐화한다.
- 해당 파일을 Unity Build에서 제외한다.

### 어떤 파일은 일반 빌드에서 깨지고 Unity Build에서는 통과한다

원인:

다른 파일이 먼저 include한 헤더에 우연히 의존하고 있을 가능성이 큽니다.

해결:

- 해당 `.cpp`가 직접 사용하는 타입과 함수의 헤더를 직접 include한다.
- include-what-you-use 같은 도구를 검토한다.
- CI에서 일반 빌드를 함께 유지한다.

### 매크로 때문에 이상한 컴파일 오류가 난다

원인:

앞 파일에서 정의한 매크로가 뒤 파일에 영향을 주고 있을 수 있습니다.

해결:

```cpp
#define SOME_OPTION 1
#include "SomeHeader.h"
#undef SOME_OPTION
```

또는 해당 파일을 Unity Build에서 제외합니다.

### 메모리 사용량이 너무 커진다

원인:

Unity Build 묶음 크기가 너무 클 수 있습니다.
하나의 거대한 translation unit은 컴파일러 메모리 사용량을 크게 늘릴 수 있습니다.

해결:

- `UNITY_BUILD_BATCH_SIZE`를 줄인다.
- 빌드 병렬도와 묶음 크기를 함께 조절한다.
- 메모리가 부족한 CI 환경에서는 Unity Build를 제한적으로 사용한다.

---

## 14. Unity Build 적용 체크리스트

Unity Build를 도입하기 전에 아래 항목을 확인하면 좋습니다.

- 현재 클린 빌드 시간과 증분 빌드 시간을 측정했는가?
- Unity Build를 켰을 때 실제로 얼마나 빨라지는지 비교했는가?
- 한 파일 수정 시 증분 빌드 시간이 나빠지지 않는가?
- 일반 빌드도 CI에서 유지되는가?
- 매크로를 정의한 뒤 정리하지 않는 코드가 많은가?
- 익명 namespace 안의 흔한 함수 이름이 많은가?
- generated source나 platform-specific source를 따로 관리하는가?
- Unity Build 제외 파일 목록을 관리할 기준이 있는가?
- 릴리즈 빌드에서 Unity Build를 쓸지 정책이 정해졌는가?

---

## 15. 결론

Unity Build는 C/C++ 프로젝트의 빌드 시간을 줄이는 강력한 방법입니다.
여러 `.cpp` 파일을 하나의 translation unit으로 묶어 공통 헤더 파싱, 컴파일러 실행, 반복적인 전처리 비용을 줄입니다.

하지만 모든 프로젝트에 무조건 좋은 방법은 아닙니다.
증분 빌드가 느려질 수 있고, 매크로 오염, 심볼 충돌, include 누락 은폐, ODR 문제 같은 부작용도 있습니다.

가장 좋은 접근은 아래처럼 정리할 수 있습니다.

```text
1. 먼저 빌드 시간을 측정한다.
2. 작은 타겟부터 Unity Build를 켠다.
3. 문제가 되는 파일은 제외한다.
4. 일반 빌드도 CI에서 유지한다.
5. 프로젝트에 맞는 batch size를 찾는다.
```

Unity Build는 코드 품질 문제를 해결해주는 도구가 아니라, 빌드 구조를 바꿔 시간을 줄이는 도구입니다.
잘 관리된 C++ 프로젝트에서는 큰 효과를 낼 수 있지만, 숨은 의존성이 많은 프로젝트에서는 오히려 문제를 드러냅니다.

그래서 Unity Build를 도입할 때의 핵심은 "켜느냐 마느냐"가 아니라, **어디에 켜고, 어디에는 끄며, 일반 빌드와 어떻게 함께 검증할 것인가**입니다.
