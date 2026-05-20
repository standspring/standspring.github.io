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

C와 C++의 빌드 모델은 오래된 파일 단위 컴파일 구조를 기반으로 합니다.
각 `.cpp` 파일은 독립적인 `translation unit`으로 컴파일되고, 마지막에 링커가 여러 object file을 합쳐 실행 파일이나 라이브러리를 만듭니다.

```text
전처리 -> 컴파일 -> 어셈블 -> 링크
```

이 구조는 증분 빌드와 병렬 빌드에 유리합니다.
파일 하나를 수정하면 보통 그 파일과 직접 관련된 부분만 다시 컴파일하면 됩니다.

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

일반 빌드에서는 각 소스 파일을 따로 컴파일하므로 컴파일러는 비슷한 헤더 트리를 여러 번 처리합니다.

```text
a.cpp 컴파일: vector, string, map, Common.h, Logger.h, Config.h 처리
b.cpp 컴파일: vector, string, map, Common.h, Logger.h, Config.h 처리
c.cpp 컴파일: vector, string, map, Common.h, Logger.h, Config.h 처리
```

소스 파일이 10개 정도라면 큰 문제가 아닐 수 있습니다.
하지만 소스 파일이 수백 개, 수천 개가 되고 템플릿과 매크로가 많은 C++ 프로젝트가 되면 이 반복 비용이 빌드 시간의 큰 비중을 차지합니다.

특히 C++은 아래 이유로 컴파일 시간이 쉽게 커집니다.

- 표준 라이브러리 헤더가 크다.
- 템플릿 인스턴스화 비용이 크다.
- 헤더 파일에 구현이 들어가는 경우가 많다.
- 전처리기가 include 트리를 매번 펼친다.
- 매크로와 조건부 컴파일이 많으면 파싱 비용이 늘어난다.
- 각 translation unit마다 컴파일러 초기화와 최적화 비용이 반복된다.

결국 대규모 C++ 프로젝트에서는 빌드 시간이 개발 생산성의 병목이 됩니다.

```text
코드 수정 1분
빌드 대기 10분
테스트 실행 5분
다시 수정
다시 대기
```

이 흐름이 반복되면 개발자는 작은 수정을 빠르게 검증하기 어렵습니다.
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
  -> #include "a.cpp"
  -> #include "b.cpp"
  -> #include "c.cpp"

unity_1.cpp
  -> #include "d.cpp"
  -> #include "e.cpp"
  -> #include "f.cpp"
```

결과적으로 object file 수도 줄어듭니다.

```text
일반 빌드: a.o, b.o, c.o, d.o, e.o, f.o
Unity Build: unity_0.o, unity_1.o
```

빌드 시스템이 Unity Build를 지원하는 경우, 개발자가 직접 `unity_0.cpp`를 작성할 필요는 없습니다.
CMake, Unreal Build Tool, Chromium의 Jumbo Build 같은 시스템이 내부적으로 이런 파일을 생성하거나 유사한 방식으로 묶어줍니다.

---

## 3. 왜 빨라지는가

Unity Build가 빨라지는 이유는 단순히 파일 수가 줄어서만은 아닙니다.
실제로는 여러 비용이 함께 줄어듭니다.

### 3-1. 헤더 파싱 반복 감소

C++ 컴파일 시간의 큰 부분은 헤더를 읽고 파싱하는 데 사용됩니다.
같은 헤더가 여러 `.cpp`에서 반복적으로 include되면 컴파일러는 그 작업을 translation unit마다 다시 수행합니다.

`#pragma once`나 include guard는 같은 translation unit 안에서 중복 include를 막아줄 뿐입니다.
서로 다른 `.cpp` 파일 사이의 반복 파싱 비용까지 없애주지는 못합니다.

Unity Build에서는 여러 `.cpp`가 하나의 translation unit 안에 들어가므로 공통 헤더 처리 비용이 줄어들 수 있습니다.

### 3-2. 컴파일러 실행 비용 감소

소스 파일이 많으면 컴파일러 프로세스 실행도 많아집니다.
각 실행에는 옵션 해석, 파일 열기, 전처리 환경 구성, 내부 자료구조 초기화 같은 고정 비용이 있습니다.

Unity Build는 컴파일 단위를 줄이므로 이런 고정 비용도 함께 줄입니다.

### 3-3. 템플릿 처리 비용 감소

C++ 프로젝트는 템플릿 코드가 많습니다.
일반 빌드에서는 비슷한 템플릿 인스턴스가 여러 translation unit에서 반복 처리될 수 있습니다.

Unity Build에서는 같은 translation unit 안에서 처리되는 코드 범위가 넓어지므로 일부 반복 비용이 줄어들 수 있습니다.

### 3-4. 링크 입력 파일 수 감소

object file 수가 줄어들면 링커가 다루는 입력 파일 수도 줄어듭니다.
프로젝트에 따라 링크 시간이 어느 정도 줄어들 수 있습니다.

다만 Unity Build의 주된 효과는 보통 링크보다 컴파일 단계에서 나타납니다.

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

일반 빌드에서는 각각 컴파일합니다.

```bash
g++ -c src/main.cpp -o main.o
g++ -c src/math.cpp -o math.o
g++ -c src/string_util.cpp -o string_util.o
g++ -c src/file_util.cpp -o file_util.o
g++ main.o math.o string_util.o file_util.o -o app
```

Unity Build에서는 이런 임시 파일이 만들어질 수 있습니다.

```cpp
// unity.cpp
#include "src/main.cpp"
#include "src/math.cpp"
#include "src/string_util.cpp"
#include "src/file_util.cpp"
```

그리고 이 파일 하나를 컴파일합니다.

```bash
g++ -c unity.cpp -o unity.o
g++ unity.o -o app
```

실무에서는 직접 이런 파일을 관리하기보다 빌드 시스템에 맡기는 편이 좋습니다.
직접 관리하면 파일 추가, 제외, 플랫폼별 조건, 디버그 설정을 관리하기 어려워집니다.

---

## 5. CMake에서 Unity Build 사용하기

CMake는 `UNITY_BUILD` 속성을 지원합니다.
target 단위로 아래처럼 설정할 수 있습니다.

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

프로젝트 전체 기본값으로 켜고 싶다면 아래처럼 설정할 수도 있습니다.

```cmake
set(CMAKE_UNITY_BUILD ON)
```

다만 처음부터 전체 프로젝트에 켜는 것은 추천하지 않습니다.
먼저 특정 라이브러리나 실행 파일 하나에 적용해보고 문제가 없는지 확인하는 방식이 좋습니다.

### 묶음 크기 조절

CMake에서는 하나의 unity source에 몇 개의 원본 소스 파일을 묶을지 조절할 수 있습니다.

```cmake
set_target_properties(my_app PROPERTIES
    UNITY_BUILD ON
    UNITY_BUILD_BATCH_SIZE 8
)
```

`BATCH_SIZE`가 너무 크면 파일 하나를 수정했을 때 다시 컴파일해야 하는 범위가 커집니다.
반대로 너무 작으면 Unity Build의 효과가 줄어듭니다.

처음에는 `4`, `8`, `16` 정도를 비교해보는 것이 좋습니다.

### 특정 파일 제외

Unity Build에 포함하면 문제가 생기는 파일은 제외할 수 있습니다.

```cmake
set_source_files_properties(src/special_case.cpp PROPERTIES
    SKIP_UNITY_BUILD_INCLUSION ON
)
```

매크로 충돌, 전역 심볼 충돌, 플랫폼별 조건이 복잡한 파일, generated source는 이렇게 별도로 관리하는 편이 안전합니다.

---

## 6. Unity Build의 장점

### 6-1. 전체 빌드 시간이 줄어들 수 있다

가장 큰 장점은 clean build 시간 단축입니다.
대규모 C++ 프로젝트에서 Unity Build를 켰을 때 전체 빌드 시간이 크게 줄어드는 경우가 많습니다.

특히 아래 조건에 해당하면 효과가 커질 수 있습니다.

- `.cpp` 파일 수가 많다.
- 공통 헤더가 크다.
- include 트리가 깊다.
- 템플릿 라이브러리를 많이 쓴다.
- CI에서 clean build를 자주 수행한다.

### 6-2. CI 비용을 줄일 수 있다

CI 서버에서 전체 빌드를 자주 수행한다면 빌드 시간은 곧 비용입니다.
빌드 시간이 30분에서 15분으로 줄어들면 피드백도 빨라지고 컴퓨팅 자원도 아낄 수 있습니다.

PR 검증 시간이 줄어들면 코드 리뷰와 수정 흐름도 좋아집니다.

### 6-3. 일부 최적화 기회가 늘 수 있다

여러 소스 파일이 하나의 translation unit에 들어가면 컴파일러가 더 넓은 범위의 코드를 볼 수 있습니다.
그 결과 일부 함수 인라이닝이나 dead code 제거가 가능해질 수 있습니다.

다만 이것을 Unity Build의 주된 목적이라고 보기는 어렵습니다.
실행 성능 최적화가 목적이라면 LTO(Link Time Optimization)를 별도로 검토하는 편이 더 적절합니다.

### 6-4. 숨은 include 누락을 발견할 수도 있다

Unity Build는 include 순서를 바꾸거나 파일을 섞으면서 어떤 파일이 우연히 다른 파일의 헤더에 의존하고 있었다는 사실을 드러낼 수 있습니다.

이런 오류는 귀찮아 보이지만 실제로는 코드의 독립성이 깨져 있었다는 신호입니다.

---

## 7. Unity Build의 단점

Unity Build는 강력하지만 공짜는 아닙니다.
C++의 이름 규칙, 전처리기, 전역 상태가 한 translation unit 안에서 섞이기 때문에 예상하지 못한 문제가 생길 수 있습니다.

### 7-1. 증분 빌드가 느려질 수 있다

Unity Build는 여러 `.cpp`를 하나로 묶습니다.
따라서 그 묶음 안의 파일 하나만 수정해도 묶음 전체를 다시 컴파일해야 합니다.

```cpp
// unity_0.cpp
#include "a.cpp"
#include "b.cpp"
#include "c.cpp"
#include "d.cpp"
#include "e.cpp"
```

이때 `c.cpp` 한 줄만 수정해도 `a.cpp`부터 `e.cpp`까지 포함된 unity translation unit이 다시 컴파일됩니다.

그래서 Unity Build는 clean build나 CI에는 유리하지만, 로컬에서 파일 하나를 자주 수정하는 개발 흐름에는 불리할 수 있습니다.

### 7-2. 매크로 누수가 발생할 수 있다

Unity Build에서는 여러 `.cpp`가 같은 translation unit에 들어갑니다.
따라서 한 파일에서 정의한 매크로가 뒤에 include되는 파일에 영향을 줄 수 있습니다.

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
하지만 Unity Build에서 `a.cpp` 다음에 `b.cpp`가 포함되면 매크로가 살아 있는 상태로 `b.cpp`가 처리될 수 있습니다.

이런 코드는 반드시 정리해야 합니다.

```cpp
#define SOME_OPTION 1
#include "SomeHeader.h"
#undef SOME_OPTION
```

### 7-3. 익명 namespace와 static 심볼 충돌이 생길 수 있다

일반 빌드에서는 각 `.cpp` 파일이 서로 다른 translation unit입니다.
그래서 각 파일 안에 같은 이름의 `static` 함수나 익명 namespace 내부 함수가 있어도 충돌하지 않습니다.

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
하지만 Unity Build에서 두 파일이 같은 translation unit에 들어오면 재정의 오류가 발생할 수 있습니다.

해결 방법은 이름을 더 구체적으로 바꾸거나, 문제가 되는 파일을 Unity Build에서 제외하는 것입니다.

### 7-4. include 의존성이 가려질 수 있다

Unity Build에서는 앞에 포함된 `.cpp`가 이미 어떤 헤더를 include했기 때문에 뒤 파일이 우연히 컴파일될 수 있습니다.

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

> 내가 쓰는 것은 내가 include한다.

### 7-5. 빌드 오류 위치와 디버깅이 헷갈릴 수 있다

컴파일러가 생성된 `unity_0.cpp`를 기준으로 오류를 보고하면 원본 파일 위치를 추적하기 번거로울 수 있습니다.
빌드 시스템과 IDE가 잘 지원하면 괜찮지만, 환경에 따라 오류 메시지가 덜 직관적으로 보일 수 있습니다.

### 7-6. 병렬 빌드 효율이 떨어질 수 있다

일반 빌드에서는 많은 `.cpp` 파일을 여러 CPU 코어에 나누어 컴파일할 수 있습니다.

```text
16개 코어 -> 16개 .cpp 동시 컴파일
```

Unity Build에서 너무 크게 묶으면 컴파일 단위 수가 줄어 병렬화할 작업이 부족해질 수 있습니다.

```text
16개 코어 -> unity_0.cpp, unity_1.cpp만 컴파일
```

따라서 묶음 크기는 프로젝트 규모와 빌드 머신의 코어 수를 고려해서 조절해야 합니다.

---

## 8. Unity Build가 잘 맞는 프로젝트

Unity Build는 아래 프로젝트에 잘 맞습니다.

- C++ 소스 파일 수가 많다.
- clean build 시간이 길다.
- CI에서 전체 빌드가 자주 돈다.
- 공통 헤더가 크고 include 트리가 복잡하다.
- 파일별 매크로 상태가 비교적 깨끗하다.
- 파일별 독립성이 잘 지켜져 있다.
- 빌드 시간 단축이 생산성에 큰 영향을 준다.

게임 엔진, 브라우저, 대형 데스크톱 애플리케이션, 임베디드 SDK, 대형 라이브러리에서 검토할 만합니다.

---

## 9. Unity Build가 잘 맞지 않는 프로젝트

반대로 아래 상황에서는 조심해야 합니다.

- 파일마다 매크로 상태가 복잡하게 다르다.
- `static` 함수나 익명 namespace에 같은 이름이 많다.
- 전역 변수와 전역 매크로가 많다.
- 대부분의 개발자가 로컬에서 작은 파일 하나만 자주 수정한다.
- 일반 빌드가 이미 충분히 빠르다.
- 빌드 오류 분석 도구가 Unity Build를 잘 지원하지 않는다.
- 코드 위생이 낮아 파일 간 숨은 의존성이 많다.

이런 프로젝트에서 무리하게 Unity Build를 켜면 빌드 속도는 조금 좋아져도 유지보수 비용이 커질 수 있습니다.

---

## 10. Unity Build와 PCH 비교

Unity Build와 PCH(Precompiled Header)는 모두 빌드 시간을 줄이는 방법이지만 접근 방식이 다릅니다.

| 구분 | Unity Build | Precompiled Header |
|---|---|---|
| 핵심 아이디어 | 여러 `.cpp`를 하나로 묶음 | 자주 쓰는 헤더를 미리 컴파일 |
| 주요 효과 | translation unit 수 감소 | 헤더 파싱 비용 감소 |
| 장점 | 설정이 비교적 단순하고 효과가 큰 경우가 많음 | 소스 파일 경계를 유지함 |
| 단점 | 매크로 누수, 심볼 충돌, 증분 빌드 악화 가능 | PCH 구성 관리가 필요함 |
| 추천 사용 | clean build, CI 최적화 | 로컬 개발과 전체 빌드 모두에 유용 |

둘은 경쟁 관계라기보다 함께 사용할 수 있는 도구입니다.
대형 프로젝트에서는 PCH, ccache/sccache, Ninja, 병렬 빌드, Unity Build를 조합해서 사용합니다.

---

## 11. Unity Build와 LTO 비교

LTO(Link Time Optimization)는 링크 단계에서 여러 object file을 함께 분석하고 최적화하는 기법입니다.

Unity Build와 LTO는 목적이 다릅니다.

| 구분 | Unity Build | LTO |
|---|---|---|
| 주 목적 | 빌드 시간 단축 | 실행 파일 최적화 |
| 적용 단계 | 컴파일 단계 | 링크 단계 |
| 코드 경계 | 여러 `.cpp`를 한 translation unit으로 묶음 | object file 경계를 넘어 최적화 |
| 빌드 시간 영향 | clean build가 빨라질 수 있음 | 링크 시간이 늘 수 있음 |
| 출력물 성능 | 일부 개선 가능하지만 주 목적은 아님 | 성능과 크기 개선 가능 |

실행 성능 최적화가 목적이라면 LTO를 검토하고, 빌드 대기 시간이 문제라면 Unity Build를 검토하는 식으로 구분하면 됩니다.

---

## 12. 실무 적용 전략

Unity Build는 한 번에 전체 프로젝트에 켜기보다 단계적으로 적용하는 편이 좋습니다.

### 12-1. 현재 빌드 시간을 먼저 측정한다

최적화는 측정부터 시작해야 합니다.

```text
일반 clean build 시간
일반 incremental build 시간
Unity Build clean build 시간
Unity Build incremental build 시간
CI 빌드 시간
로컬 빌드 시간
```

측정 없이 "빨라질 것이다"라고 가정하면 잘못된 결정을 하기 쉽습니다.

### 12-2. 작은 target부터 켠다

처음에는 전체 프로젝트가 아니라 특정 라이브러리 하나에만 적용합니다.

```cmake
set_target_properties(core_lib PROPERTIES UNITY_BUILD ON)
```

문제가 없다면 다른 target으로 넓혀갑니다.

### 12-3. 문제 파일은 제외한다

Unity Build에서 자주 문제를 일으키는 파일은 과감하게 제외하는 편이 좋습니다.

```cmake
set_source_files_properties(src/legacy_macro_heavy.cpp PROPERTIES
    SKIP_UNITY_BUILD_INCLUSION ON
)
```

100% 최적화보다 안정적으로 유지되는 80% 최적화가 더 나을 때가 많습니다.

### 12-4. 일반 빌드도 유지한다

Unity Build만 CI에서 돌리면 include 누락 같은 문제가 가려질 수 있습니다.
가능하면 일반 빌드도 별도 job으로 유지하는 것이 좋습니다.

추천 구성은 아래와 같습니다.

```text
PR 빠른 검증: Unity Build ON
야간 빌드: Unity Build OFF + 전체 테스트
릴리즈 빌드: 프로젝트 정책에 따라 ON/OFF 고정
```

### 12-5. 코드 규칙을 정리한다

Unity Build를 안정적으로 쓰려면 코드 위생이 중요합니다.

- `.cpp`는 자신이 쓰는 헤더를 직접 include한다.
- 매크로를 정의했다면 가능한 빨리 `#undef`한다.
- 전역 변수와 전역 상태를 줄인다.
- 익명 namespace 안의 이름도 너무 일반적으로 짓지 않는다.
- 파일 include 순서에 의존하지 않는다.
- generated file, platform-specific file, legacy file은 별도 관리한다.

---

## 13. 자주 만나는 오류와 해결 방법

### 같은 이름의 함수가 재정의된다는 오류

원인은 보통 익명 namespace나 `static` 함수 이름 충돌입니다.

```cpp
namespace {
void Init() {}
}
```

여러 파일에 같은 이름이 있고 Unity Build에서 같은 translation unit으로 묶이면 충돌할 수 있습니다.

해결 방법은 이름을 구체적으로 바꾸거나, 해당 파일을 Unity Build에서 제외하는 것입니다.

### Unity Build에서는 통과하는데 일반 빌드에서는 깨진다

어떤 파일이 필요한 헤더를 직접 include하지 않고 다른 파일이 먼저 include한 헤더에 우연히 의존하고 있을 가능성이 큽니다.

해결 방법은 해당 `.cpp`가 직접 사용하는 타입과 함수의 헤더를 직접 include하는 것입니다.

### 매크로 때문에 이상한 컴파일 오류가 난다

한 파일에서 정의한 매크로가 다음 파일까지 영향을 주고 있을 수 있습니다.

```cpp
#define SOME_OPTION 1
#include "SomeHeader.h"
#undef SOME_OPTION
```

매크로 범위를 최대한 짧게 만들거나 문제가 되는 파일을 Unity Build에서 제외합니다.

### 메모리 사용량이 너무 커진다

묶음 크기가 너무 클 수 있습니다.
`UNITY_BUILD_BATCH_SIZE`를 줄이고 빌드 병렬도와 함께 조절합니다.

---

## 14. Unity Build 적용 체크리스트

Unity Build를 도입하기 전에 아래 항목을 확인하면 좋습니다.

- 현재 clean build 시간과 incremental build 시간을 측정했는가?
- Unity Build를 켰을 때 실제로 얼마나 빨라지는지 비교했는가?
- 파일 하나 수정 후 증분 빌드 시간이 과도하게 늘지 않는가?
- 일반 빌드도 CI에서 주기적으로 유지하는가?
- 매크로를 정의하고 정리하지 않는 코드가 많지 않은가?
- 익명 namespace 안의 흔한 함수 이름이 많지 않은가?
- generated source와 platform-specific source를 별도로 관리하는가?
- Unity Build 제외 파일 목록을 관리할 기준이 있는가?
- 릴리즈 빌드에서 Unity Build를 쓸지 정책을 정했는가?

---

## 15. 결론

Unity Build는 C/C++ 프로젝트의 빌드 시간을 줄이는 강력한 방법입니다.
여러 `.cpp` 파일을 하나의 translation unit으로 묶어 공통 헤더 파싱, 컴파일러 실행, 반복적인 전처리 비용을 줄입니다.

하지만 모든 프로젝트에 무조건 좋은 방법은 아닙니다.
증분 빌드가 느려질 수 있고, 매크로 누수, 심볼 충돌, include 누락 은폐 같은 부작용이 있습니다.

가장 좋은 접근은 아래처럼 정리할 수 있습니다.

```text
1. 먼저 빌드 시간을 측정한다.
2. 작은 target에 Unity Build를 켠다.
3. 문제가 되는 파일은 제외한다.
4. 일반 빌드도 CI에서 유지한다.
5. 프로젝트에 맞는 batch size를 찾는다.
```

Unity Build는 코드 설계 문제를 해결해주는 도구가 아니라, 빌드 구조를 바꿔 시간을 줄이는 도구입니다.
잘 관리된 C++ 프로젝트에서는 큰 효과를 줄 수 있지만, 숨은 의존성이 많은 프로젝트에서는 오히려 문제를 드러냅니다.

그래서 Unity Build를 도입할 때의 핵심 질문은 단순히 "켤까, 말까"가 아닙니다.

> 어디에 켜고, 어디에는 끄며, 일반 빌드는 어떻게 함께 검증할 것인가?

이 기준을 정하고 적용하면 Unity Build는 대규모 C++ 프로젝트에서 꽤 든든한 빌드 최적화 도구가 될 수 있습니다.
