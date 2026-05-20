---
title: "LTO Build Option이란? 탄생 배경부터 장단점, 실무 적용 기준까지"
description: "C/C++ 빌드 최적화 옵션인 LTO(Link Time Optimization)의 개념, 탄생 배경, 동작 원리, 장점과 단점, Unity Build와의 차이, CMake 적용 방법, 실무 체크리스트를 정리합니다."
date: 2026-05-20
categories: [C++, Build]
tags: [lto, link-time-optimization, ipo, cpp, cplusplus, cmake, compiler-optimization, build-optimization]
---

![LTO Build Option 개념도](/assets/img/2026-05-20-lto-build-option.svg)

`LTO(Link Time Optimization)`는 말 그대로 **링크 단계에서 수행하는 최적화**입니다.

일반적인 C/C++ 빌드에서는 각 `.cpp` 파일이 독립적으로 컴파일되어 object file이 되고, 마지막에 링커가 이 object file들을 합쳐 실행 파일이나 라이브러리를 만듭니다.

```text
a.cpp -> a.o
b.cpp -> b.o
c.cpp -> c.o

a.o + b.o + c.o -> app
```

이 방식은 오래되고 안정적이지만 한 가지 큰 한계가 있습니다.

컴파일러는 `a.cpp`를 컴파일할 때 `b.cpp` 안의 구현을 잘 모릅니다.
`b.cpp`를 컴파일할 때도 `a.cpp` 안의 구현을 잘 모릅니다.
즉, 각 translation unit 단위로는 똑똑하게 최적화할 수 있지만, **프로그램 전체를 보고 최적화하기는 어렵습니다.**

LTO는 이 경계를 늦춥니다.

컴파일 단계에서 최종 기계어만 바로 만들지 않고, 최적화에 필요한 중간 표현을 object file 안에 남겨 둡니다.
그리고 링크 단계에서 여러 object file을 함께 보면서 함수 인라이닝, 죽은 코드 제거, 전역 최적화 같은 작업을 더 넓은 범위로 수행합니다.

```text
a.cpp -> a.o, 최적화용 중간 표현 포함
b.cpp -> b.o, 최적화용 중간 표현 포함
c.cpp -> c.o, 최적화용 중간 표현 포함

링크 단계에서 a.o, b.o, c.o를 함께 분석
-> 프로그램 전체 관점의 최적화
-> app
```

짧게 말하면 이렇습니다.

> LTO는 컴파일러가 파일 하나하나만 보는 대신, 링크 시점에 프로그램 전체를 더 넓게 보고 최적화하게 만드는 빌드 옵션입니다.

---

## 1. LTO가 탄생한 배경

C와 C++의 전통적인 빌드 모델은 파일 단위 컴파일을 중심으로 설계되었습니다.
각 `.cpp` 파일은 독립적인 translation unit으로 처리되고, 그 결과물이 object file로 저장됩니다.

```text
전처리 -> 컴파일 -> 어셈블 -> object file 생성 -> 링크
```

이 구조는 장점이 많습니다.

- 파일 하나만 수정하면 해당 파일만 다시 컴파일할 수 있습니다.
- 여러 파일을 병렬로 컴파일하기 쉽습니다.
- object file과 정적 라이브러리를 재사용하기 좋습니다.
- 빌드 시스템이 의존성을 관리하기 쉽습니다.

하지만 프로그램 규모가 커지고 C++ 코드가 복잡해지면서 이 모델의 약점도 커졌습니다.

예를 들어 아래처럼 `main.cpp`에서 `math.cpp`의 함수를 호출한다고 가정해보겠습니다.

```cpp
// math.h
int square(int value);
```

```cpp
// math.cpp
int square(int value)
{
    return value * value;
}
```

```cpp
// main.cpp
#include "math.h"

int main()
{
    return square(10);
}
```

일반적인 컴파일에서 `main.cpp`를 컴파일하는 시점에는 `square()`의 선언만 보입니다.
구현이 `return value * value;`라는 사실은 `math.cpp` 안에 있습니다.

따라서 컴파일러는 `main.cpp`를 컴파일할 때 보수적으로 코드를 생성해야 합니다.

```text
main.cpp 입장:
square라는 함수가 있다.
하지만 내부 구현은 지금 모른다.
그러니 함수 호출 코드를 남긴다.
```

반면 `math.cpp`를 컴파일하는 시점에는 `square()`가 어디서 어떻게 호출되는지 충분히 알기 어렵습니다.

```text
math.cpp 입장:
square의 구현은 안다.
하지만 호출하는 쪽의 문맥은 모른다.
```

이렇게 파일 경계가 강하면 컴파일러가 놓치는 최적화 기회가 생깁니다.

- 아주 작은 함수를 다른 파일에서 호출할 때 인라이닝하기 어렵습니다.
- 실제로 쓰이지 않는 전역 함수나 전역 객체를 제거하기 어렵습니다.
- 함수 인자 값의 범위나 호출 패턴을 프로그램 전체 기준으로 추론하기 어렵습니다.
- 가상 함수 호출, 함수 포인터 호출, 템플릿 코드의 최적화 기회가 제한됩니다.
- 라이브러리 내부 구현과 호출 지점을 함께 보지 못합니다.

그래서 등장한 아이디어가 **Whole Program Optimization**, 또는 **Interprocedural Optimization**입니다.
프로그램 전체, 또는 여러 함수와 여러 파일을 가로질러 최적화하자는 접근입니다.

LTO는 이 아이디어를 현실적인 C/C++ 빌드 파이프라인 안에 넣은 방식입니다.

---

## 2. LTO, IPO, WPO의 관계

비슷한 용어가 여러 개 나오기 때문에 먼저 정리해두는 편이 좋습니다.

| 용어 | 의미 |
|---|---|
| LTO | Link Time Optimization. 링크 단계에서 수행하는 최적화 |
| IPO | Interprocedural Optimization. 함수 경계를 넘어 수행하는 최적화 |
| WPO | Whole Program Optimization. 프로그램 전체를 대상으로 수행하는 최적화 |

세 용어는 완전히 같은 말은 아니지만 실무에서는 많이 겹쳐서 쓰입니다.

LTO는 구현 방식에 가까운 표현입니다.
링크 단계에서 최적화한다는 빌드 파이프라인의 위치를 강조합니다.

IPO는 최적화 범위에 가까운 표현입니다.
한 함수 안에서만 최적화하는 것이 아니라 함수와 함수 사이의 관계까지 분석한다는 뜻입니다.

WPO는 더 큰 관점의 표현입니다.
프로그램 전체를 하나의 대상으로 보고 최적화한다는 의미입니다.

CMake에서는 이 기능을 보통 `INTERPROCEDURAL_OPTIMIZATION`이라는 속성으로 다룹니다.
즉, CMake 설정에서는 IPO라는 이름을 사용하지만, 실제로는 컴파일러와 링커의 LTO 기능을 켜는 경우가 많습니다.

---

## 3. 일반 빌드와 LTO 빌드의 차이

일반적인 최적화 빌드는 대략 이런 흐름입니다.

```text
1. a.cpp를 최적화해서 a.o 생성
2. b.cpp를 최적화해서 b.o 생성
3. c.cpp를 최적화해서 c.o 생성
4. 링커가 a.o, b.o, c.o를 합침
```

이때 각 `.cpp` 파일의 최적화는 주로 해당 translation unit 안에서 이루어집니다.
링커는 보통 심볼을 연결하고, 주소를 배치하고, 필요한 라이브러리를 묶는 역할에 집중합니다.

LTO 빌드는 흐름이 조금 다릅니다.

```text
1. a.cpp를 컴파일하되 최적화용 중간 표현을 a.o에 보관
2. b.cpp를 컴파일하되 최적화용 중간 표현을 b.o에 보관
3. c.cpp를 컴파일하되 최적화용 중간 표현을 c.o에 보관
4. 링크 단계에서 중간 표현을 함께 읽음
5. 여러 파일을 가로질러 최적화
6. 최종 기계어 생성 및 링크
```

여기서 말하는 중간 표현은 컴파일러마다 다릅니다.

- GCC는 GIMPLE 계열의 LTO 정보를 사용합니다.
- Clang/LLVM은 LLVM bitcode를 활용합니다.
- MSVC는 `/GL`, `/LTCG` 조합으로 링크 타임 코드 생성을 수행합니다.

핵심은 같습니다.

> LTO용 object file은 단순한 기계어 덩어리가 아니라, 링크 시점에 다시 최적화할 수 있는 정보를 포함합니다.

---

## 4. LTO가 가능하게 만드는 최적화

LTO를 켰다고 항상 성능이 극적으로 좋아지는 것은 아닙니다.
하지만 컴파일러가 볼 수 있는 정보가 늘어나므로 여러 최적화 기회가 생깁니다.

### 4-1. 파일 경계를 넘는 함수 인라이닝

가장 대표적인 효과는 cross translation unit inlining입니다.

일반 빌드에서는 `main.cpp`에서 `math.cpp`의 작은 함수를 호출해도 구현을 볼 수 없어서 인라이닝하지 못할 수 있습니다.

LTO를 켜면 링크 단계에서 두 파일의 정보를 함께 볼 수 있습니다.
그러면 이런 판단이 가능해집니다.

```text
square()는 매우 작다.
호출 지점도 명확하다.
함수 호출 비용보다 인라이닝 이득이 크다.
그러니 main() 안으로 펼쳐 넣자.
```

결과적으로 함수 호출 오버헤드가 줄고, 인라이닝된 코드 주변에서 추가 최적화가 이어질 수 있습니다.

```cpp
int main()
{
    return square(10);
}
```

위 코드는 최적화 후 아래와 비슷한 형태가 될 수 있습니다.

```cpp
int main()
{
    return 100;
}
```

실제로 생성되는 기계어는 컴파일러와 옵션에 따라 다르지만, 개념적으로는 이런 방향입니다.

### 4-2. 죽은 코드 제거

파일 단위 컴파일에서는 어떤 전역 함수가 다른 object file에서 호출될 가능성을 쉽게 배제하기 어렵습니다.
그래서 보수적으로 남겨두는 코드가 생깁니다.

LTO는 프로그램 전체 호출 관계를 더 넓게 볼 수 있으므로 실제로 사용되지 않는 함수, 변수, 템플릿 인스턴스, 정적 초기화 코드를 제거할 가능성이 커집니다.

이 효과는 실행 파일 크기 감소로 이어질 수 있습니다.
특히 아래 상황에서 도움이 됩니다.

- 템플릿 코드가 많은 프로젝트
- 헤더 온리 라이브러리를 많이 사용하는 프로젝트
- 큰 정적 라이브러리를 일부 기능만 사용하는 프로젝트
- 임베디드처럼 바이너리 크기가 중요한 프로젝트

### 4-3. 상수 전파와 분기 제거

함수 호출 경계를 넘어 값이 추적되면 더 많은 상수 전파가 가능해집니다.

```cpp
// config.cpp
bool isFeatureEnabled()
{
    return false;
}
```

```cpp
// feature.cpp
void run()
{
    if (isFeatureEnabled()) {
        runExpensiveFeature();
    }
}
```

일반 빌드에서는 `run()`을 컴파일할 때 `isFeatureEnabled()`의 결과를 확정하기 어렵습니다.
LTO에서는 두 구현을 함께 보면서 분기를 제거할 수 있는 경우가 생깁니다.

```text
isFeatureEnabled()는 항상 false를 반환한다.
그러면 runExpensiveFeature() 호출 경로는 제거할 수 있다.
```

### 4-4. 가상 함수 호출 최적화

C++에서 가상 함수 호출은 런타임 다형성을 위해 필요하지만, 직접 호출보다 비쌀 수 있습니다.
컴파일러가 실제 타입을 확신할 수 있다면 가상 호출을 직접 호출로 바꾸거나 인라이닝할 수 있습니다.
이 작업을 devirtualization이라고 부릅니다.

LTO는 클래스 계층, 생성 지점, 호출 지점 정보를 더 넓게 볼 수 있으므로 devirtualization 기회가 늘어날 수 있습니다.

다만 C++의 동적 로딩, 공유 라이브러리 경계, 심볼 가시성, 상속 구조 때문에 항상 가능한 것은 아닙니다.

### 4-5. 전역 변수와 정적 초기화 최적화

프로그램 전체 관점에서 전역 객체가 실제로 어떻게 사용되는지 더 잘 보이면 초기화 코드나 접근 코드를 줄일 수 있습니다.
특히 정적 라이브러리와 결합될 때 사용하지 않는 전역 코드가 제거되면서 바이너리가 작아지는 경우가 있습니다.

---

## 5. LTO의 장점

### 5-1. 실행 성능이 좋아질 수 있다

LTO의 가장 큰 목적은 실행 파일의 성능 개선입니다.
파일 경계를 넘는 인라이닝, 죽은 코드 제거, 상수 전파, devirtualization이 잘 맞아떨어지면 런타임 성능이 좋아질 수 있습니다.

특히 작은 함수 호출이 많은 코드, 추상화 계층이 두꺼운 C++ 코드, 템플릿 기반 코드에서는 효과를 볼 가능성이 있습니다.

하지만 항상 빨라지는 것은 아닙니다.
인라이닝이 늘어나면서 instruction cache 사용이 나빠질 수도 있고, 컴파일러의 비용 모델이 모든 상황에서 완벽한 것도 아닙니다.

그래서 LTO는 반드시 벤치마크로 확인해야 합니다.

### 5-2. 바이너리 크기가 줄어들 수 있다

사용하지 않는 코드 제거가 더 잘 되면 실행 파일이나 라이브러리 크기가 줄어들 수 있습니다.
임베디드, 모바일, 플러그인, 게임 콘솔, 배포 파일 크기가 중요한 환경에서는 이 장점이 꽤 큽니다.

크기 최적화를 원한다면 `-Os`, `-Oz`, section garbage collection, symbol visibility 설정과 함께 봐야 합니다.

예를 들어 GCC/Clang 계열에서는 아래 옵션들과 같이 검토하는 경우가 많습니다.

```bash
-ffunction-sections
-fdata-sections
-Wl,--gc-sections
-flto
```

플랫폼과 링커에 따라 지원 여부와 효과는 다릅니다.

### 5-3. 추상화 비용을 줄일 수 있다

C++에서는 성능 좋은 코드를 유지하면서도 추상화를 사용하고 싶을 때가 많습니다.
작은 래퍼 함수, 정책 클래스, 템플릿, 인터페이스 계층은 코드 구조를 좋게 만들지만 최적화가 약하면 비용이 남을 수 있습니다.

LTO는 파일 경계를 넘어 이런 추상화 계층을 더 적극적으로 제거할 수 있습니다.

즉, 설계를 조금 더 표현력 있게 가져가면서도 최종 바이너리에서는 불필요한 껍질이 사라질 가능성이 커집니다.

### 5-4. 정적 라이브러리 최적화에 유리하다

정적 라이브러리를 링크할 때 LTO 정보가 유지되어 있다면, 애플리케이션 코드와 라이브러리 코드를 함께 최적화할 수 있습니다.

예를 들어 `libcore.a` 안의 작은 함수가 애플리케이션 코드에서 자주 호출된다면, LTO를 통해 인라이닝될 수 있습니다.

다만 이 효과를 얻으려면 라이브러리도 LTO 호환 방식으로 빌드되어야 합니다.
애플리케이션만 LTO를 켠다고 모든 외부 라이브러리까지 마법처럼 최적화되는 것은 아닙니다.

---

## 6. LTO의 단점

### 6-1. 링크 시간이 길어진다

LTO는 링크 단계에서 더 많은 일을 합니다.
단순히 object file을 합치는 것이 아니라 중간 표현을 읽고, 분석하고, 최적화하고, 최종 코드를 생성합니다.

그래서 링크 시간이 늘어날 수 있습니다.

```text
일반 빌드:
컴파일 단계에서 대부분의 최적화 수행
링크 단계는 상대적으로 가벼움

LTO 빌드:
컴파일 단계 일부 작업을 링크 단계로 미룸
링크 단계가 무거워짐
```

대형 C++ 프로젝트에서는 이 차이가 꽤 크게 느껴질 수 있습니다.
특히 로컬 개발 중에 자주 링크해야 하는 실행 파일이라면 개발 피드백 속도가 나빠질 수 있습니다.

### 6-2. 메모리 사용량이 커질 수 있다

링크 단계에서 많은 모듈의 중간 표현을 동시에 분석하면 메모리를 많이 사용합니다.
대규모 프로젝트에서 LTO를 켰을 때 링커가 메모리 부족으로 실패하는 경우도 있습니다.

CI 환경에서는 특히 조심해야 합니다.
로컬 고성능 머신에서는 통과하지만, 메모리가 작은 CI runner에서는 실패할 수 있습니다.

### 6-3. 증분 빌드 경험이 나빠질 수 있다

파일 하나를 수정했는데 링크 단계에서 프로그램 전체 최적화를 다시 수행해야 한다면, 증분 빌드의 체감 속도가 느려질 수 있습니다.

LTO는 보통 release 빌드나 배포 빌드에 적합하고, 매번 빠른 피드백이 중요한 debug 빌드에는 잘 켜지 않습니다.

실무에서는 보통 이런 식으로 나눕니다.

```text
Debug: LTO OFF
RelWithDebInfo: 프로젝트 상황에 따라 선택
Release: LTO ON 검토
CI 빠른 검증: LTO OFF 또는 ThinLTO
배포 검증: LTO ON
```

### 6-4. 빌드 도구 체인의 호환성을 탄다

LTO는 컴파일러, 링커, archiver, ranlib, 정적 라이브러리, 빌드 시스템이 함께 맞아야 합니다.

예를 들어 GCC로 LTO object를 만들었는데 호환되지 않는 링커나 archiver가 중간 표현을 제대로 다루지 못하면 문제가 생길 수 있습니다.
Clang도 LTO를 제대로 쓰려면 LLVM lld 또는 gold plugin 같은 도구 체인 구성이 중요할 수 있습니다.

특히 아래 상황에서는 더 조심해야 합니다.

- 여러 컴파일러를 섞어 쓰는 프로젝트
- 외부 정적 라이브러리를 많이 링크하는 프로젝트
- 오래된 binutils를 쓰는 환경
- 크로스 컴파일 환경
- Android, iOS, 콘솔, 임베디드 같은 특수 toolchain
- prebuilt library와 직접 빌드한 library가 섞인 환경

### 6-5. 디버깅이 어려워질 수 있다

LTO는 함수 인라이닝과 코드 재배치를 더 적극적으로 수행합니다.
그래서 디버거에서 보이는 call stack, breakpoint 위치, 변수 값이 직관과 다르게 보일 수 있습니다.

물론 최적화 빌드 디버깅은 원래 어렵습니다.
LTO는 그 어려움을 조금 더 키울 수 있습니다.

`RelWithDebInfo`에 LTO를 켜는 경우에는 실제 디버깅 경험을 확인해봐야 합니다.

### 6-6. 빌드 재현성과 문제 분석이 복잡해질 수 있다

LTO를 켜면 링크 단계에서 컴파일러 최적화가 한 번 더 크게 개입합니다.
그 결과 문제가 생겼을 때 원인을 나누어 보기 어려울 수 있습니다.

```text
이 문제가 컴파일 옵션 때문인가?
링커 때문인가?
LTO plugin 때문인가?
특정 object file의 LTO 정보 때문인가?
외부 라이브러리와의 호환성 때문인가?
```

그래서 release 빌드에서 LTO를 켜더라도, 문제 분석을 위해 LTO를 끈 빌드도 쉽게 만들 수 있어야 합니다.

---

## 7. GCC와 Clang에서 LTO 사용하기

GCC와 Clang에서는 대표적으로 `-flto` 옵션을 사용합니다.

```bash
g++ -O2 -flto -c a.cpp -o a.o
g++ -O2 -flto -c b.cpp -o b.o
g++ -O2 -flto a.o b.o -o app
```

중요한 점은 컴파일 단계와 링크 단계 모두에 LTO 옵션이 들어가야 한다는 것입니다.

```text
컴파일 단계: LTO 정보를 object file에 넣기 위해 필요
링크 단계: LTO 정보를 읽고 최적화하기 위해 필요
```

실무에서는 직접 명령어를 쓰기보다 CMake, Meson, Bazel, Makefile 같은 빌드 시스템에서 설정하는 편이 안전합니다.

### GCC 예시

```bash
g++ -O3 -flto main.cpp math.cpp -o app
```

병렬 LTO를 명시하고 싶다면 환경과 버전에 따라 아래처럼 설정할 수 있습니다.

```bash
g++ -O3 -flto=auto main.cpp math.cpp -o app
```

또는 job 수를 지정할 수 있습니다.

```bash
g++ -O3 -flto=8 main.cpp math.cpp -o app
```

### Clang 예시

```bash
clang++ -O3 -flto main.cpp math.cpp -o app
```

LLVM lld를 함께 쓰는 경우:

```bash
clang++ -O3 -flto -fuse-ld=lld main.cpp math.cpp -o app
```

Clang에서는 ThinLTO도 많이 사용합니다.

```bash
clang++ -O3 -flto=thin -fuse-ld=lld main.cpp math.cpp -o app
```

ThinLTO는 full LTO보다 병렬성과 증분성에 유리하도록 설계된 방식입니다.
대형 프로젝트에서는 full LTO보다 ThinLTO가 현실적인 선택인 경우가 많습니다.

---

## 8. MSVC에서 LTO 사용하기

MSVC에서는 일반적으로 `/GL`과 `/LTCG` 조합을 사용합니다.

```bat
cl /O2 /GL /c a.cpp
cl /O2 /GL /c b.cpp
link /LTCG a.obj b.obj /OUT:app.exe
```

의미는 대략 다음과 같습니다.

| 옵션 | 의미 |
|---|---|
| `/GL` | Whole Program Optimization을 위한 정보를 object file에 포함 |
| `/LTCG` | Link Time Code Generation 수행 |

Visual Studio 프로젝트 속성에서는 보통 아래 항목과 관련됩니다.

```text
C/C++ -> Optimization -> Whole Program Optimization
Linker -> Optimization -> Link Time Code Generation
```

MSVC 환경에서는 정적 라이브러리, PDB 생성, incremental linking, LTCG 호환성까지 함께 확인해야 합니다.
특히 디버그 정보와 최적화 빌드 디버깅 경험이 프로젝트마다 다르게 느껴질 수 있습니다.

---

## 9. CMake에서 LTO 적용하기

CMake에서는 LTO를 직접 `-flto`로 넣기보다 `INTERPROCEDURAL_OPTIMIZATION` 속성을 사용하는 편이 좋습니다.

```cmake
cmake_minimum_required(VERSION 3.16)
project(LtoExample LANGUAGES CXX)

add_executable(my_app
    src/main.cpp
    src/math.cpp
)

set_target_properties(my_app PROPERTIES
    CXX_STANDARD 17
    CXX_STANDARD_REQUIRED ON
    INTERPROCEDURAL_OPTIMIZATION TRUE
)
```

특정 configuration에서만 켜고 싶다면 generator expression이나 config별 속성을 사용할 수 있습니다.

```cmake
set_property(TARGET my_app PROPERTY
    INTERPROCEDURAL_OPTIMIZATION_RELEASE TRUE
)
```

지원 여부를 확인하려면 `CheckIPOSupported` 모듈을 사용할 수 있습니다.

```cmake
include(CheckIPOSupported)
check_ipo_supported(RESULT ipo_supported OUTPUT ipo_error)

if(ipo_supported)
    set_property(TARGET my_app PROPERTY
        INTERPROCEDURAL_OPTIMIZATION_RELEASE TRUE
    )
else()
    message(WARNING "IPO/LTO is not supported: ${ipo_error}")
endif()
```

프로젝트 전체에 기본값으로 켜는 방법도 있습니다.

```cmake
set(CMAKE_INTERPROCEDURAL_OPTIMIZATION_RELEASE TRUE)
```

다만 처음부터 전체 프로젝트에 켜기보다는, 먼저 핵심 실행 파일이나 라이브러리 하나에 적용해보고 빌드 시간, 메모리, 바이너리 크기, 성능을 측정하는 편이 좋습니다.

---

## 10. Full LTO와 ThinLTO

LTO에는 구현 방식에 따라 여러 형태가 있습니다.
실무에서 자주 비교하는 것은 full LTO와 ThinLTO입니다.

### Full LTO

Full LTO는 링크 단계에서 전체 프로그램의 중간 표현을 모아 강하게 최적화하는 방식입니다.
최적화 기회는 크지만 링크 시간과 메모리 사용량이 커질 수 있습니다.

```text
장점:
최적화 범위가 넓다.
성능과 크기 최적화 기회가 크다.

단점:
링크가 무겁다.
메모리를 많이 쓸 수 있다.
대형 프로젝트에서는 부담이 크다.
```

### ThinLTO

ThinLTO는 대형 프로젝트에서 LTO를 더 현실적으로 쓰기 위해 설계된 방식입니다.
전체 모듈의 요약 정보를 먼저 만들고, 필요한 부분만 모듈 단위로 병렬 최적화합니다.

```text
장점:
full LTO보다 병렬화에 유리하다.
대형 프로젝트에서 링크 시간과 메모리 부담이 낮을 수 있다.
캐시를 활용하기 좋다.

단점:
full LTO와 최적화 결과가 완전히 같지는 않다.
toolchain 지원이 중요하다.
```

Clang/LLVM 기반 프로젝트에서는 ThinLTO를 적극적으로 검토할 만합니다.

```bash
clang++ -O2 -flto=thin -fuse-ld=lld main.cpp math.cpp -o app
```

GCC에도 LTO 파티셔닝과 병렬 LTO 옵션이 있지만, ThinLTO라는 이름의 LLVM 방식과는 구현이 다릅니다.

---

## 11. LTO와 Unity Build의 차이

LTO와 Unity Build는 둘 다 C/C++ 빌드 최적화와 관련이 있지만 목적이 다릅니다.

| 구분 | LTO | Unity Build |
|---|---|---|
| 주요 목적 | 실행 성능과 바이너리 최적화 | 컴파일 시간 단축 |
| 적용 시점 | 링크 단계 | 컴파일 단계 |
| 방식 | object file의 중간 표현을 링크 시점에 함께 최적화 | 여러 `.cpp`를 하나의 큰 translation unit처럼 묶음 |
| 빌드 시간 영향 | 보통 링크 시간이 증가 | clean build 시간이 줄 수 있음 |
| 증분 빌드 영향 | 링크가 무거워질 수 있음 | 묶음 단위 재컴파일 때문에 나빠질 수 있음 |
| 대표 위험 | toolchain 호환성, 메모리, 디버깅 어려움 | 매크로 누수, 익명 namespace 충돌, include 의존성 은폐 |

Unity Build는 주로 **컴파일을 빠르게 하기 위한 기법**입니다.
여러 `.cpp`를 묶어 공통 헤더 파싱 비용을 줄입니다.

LTO는 주로 **최종 결과물을 더 좋게 만들기 위한 기법**입니다.
링크 단계에서 파일 경계를 넘어 최적화합니다.

둘은 함께 사용할 수도 있습니다.
하지만 둘 다 빌드 구조를 크게 바꾸기 때문에 처음부터 동시에 켜면 문제 원인을 분리하기 어렵습니다.

추천 순서는 보통 이렇습니다.

```text
1. 일반 release 빌드 기준 성능과 크기를 측정한다.
2. LTO만 켜고 성능, 크기, 링크 시간을 측정한다.
3. Unity Build만 켜고 clean build, incremental build를 측정한다.
4. 둘을 함께 켠 빌드를 별도로 측정한다.
5. CI와 release 파이프라인에 맞게 조합을 정한다.
```

---

## 12. LTO와 PCH의 차이

PCH(Precompiled Header)는 자주 포함되는 헤더를 미리 컴파일해두는 방식입니다.
LTO와는 목적이 다릅니다.

| 구분 | LTO | PCH |
|---|---|---|
| 주요 목적 | 실행 성능과 바이너리 최적화 | 컴파일 시간 단축 |
| 적용 시점 | 링크 단계 | 컴파일 전반 |
| 핵심 아이디어 | 여러 object file을 함께 최적화 | 공통 헤더 파싱 비용 절약 |
| 런타임 성능 영향 | 있을 수 있음 | 거의 없음 |
| 빌드 시간 영향 | 링크 시간이 늘 수 있음 | 컴파일 시간이 줄 수 있음 |

PCH는 개발 피드백 시간을 줄이는 데 유용하고, LTO는 release 품질을 끌어올리는 데 유용합니다.
둘은 경쟁 관계라기보다 서로 다른 병목을 다루는 도구입니다.

---

## 13. 언제 LTO를 켜면 좋은가

LTO는 아래 조건에 해당할 때 검토할 만합니다.

- Release 빌드의 실행 성능이 중요하다.
- 바이너리 크기를 줄이고 싶다.
- 작은 함수 호출과 추상화 계층이 많다.
- 템플릿 기반 C++ 코드가 많다.
- 정적 라이브러리를 많이 사용한다.
- 배포 빌드 시간이 조금 늘어도 결과물 품질이 더 중요하다.
- CI에서 release 빌드를 별도로 오래 돌릴 수 있다.
- toolchain을 비교적 최신 상태로 통제할 수 있다.

특히 게임 클라이언트, 엔진 코드, 고성능 서버, 임베디드 펌웨어, CLI 도구, 모바일 앱의 native layer, 대형 C++ 라이브러리에서는 충분히 검토할 가치가 있습니다.

---

## 14. 언제 LTO를 조심해야 하는가

반대로 아래 상황에서는 신중해야 합니다.

- 로컬 개발 빌드가 이미 느린데 링크도 자주 발생한다.
- CI runner의 메모리가 부족하다.
- 외부 prebuilt library가 많고 toolchain이 제각각이다.
- 크로스 컴파일 환경이 복잡하다.
- 디버깅 가능한 release 빌드가 자주 필요하다.
- 빌드 시스템이 오래되어 컴파일 옵션과 링크 옵션을 일관되게 관리하기 어렵다.
- 빌드 재현성이 매우 중요하고 toolchain 변화에 민감하다.
- LTO를 켰을 때 성능 이득이 측정되지 않았다.

LTO는 무조건 켜야 하는 옵션이 아닙니다.
측정했을 때 이득이 있고, 비용을 감당할 수 있을 때 켜는 옵션입니다.

---

## 15. 실무 적용 전략

### 15-1. Debug에는 켜지 않는다

대부분의 프로젝트에서 debug 빌드에 LTO를 켜는 것은 추천하지 않습니다.
빌드 시간이 늘고 디버깅 경험이 나빠질 수 있기 때문입니다.

```text
Debug: OFF
Release: ON 검토
RelWithDebInfo: 필요할 때만 ON
MinSizeRel: 크기 목표가 있으면 ON 검토
```

### 15-2. 먼저 측정 기준을 만든다

LTO 적용 전후를 비교하려면 기준이 필요합니다.

```text
clean build 시간
incremental build 시간
link 시간
peak memory 사용량
실행 파일 크기
핵심 벤치마크 성능
startup time
CI 총 소요 시간
```

성능 최적화는 느낌으로 판단하면 위험합니다.
특히 LTO는 빌드 시간이 늘 수 있으므로, 실행 성능이나 바이너리 크기에서 얻는 이득이 그 비용을 정당화하는지 확인해야 합니다.

### 15-3. 타겟 단위로 켠다

처음부터 프로젝트 전체에 LTO를 켜기보다 핵심 target 하나부터 적용하는 편이 좋습니다.

```cmake
set_property(TARGET engine_runtime PROPERTY
    INTERPROCEDURAL_OPTIMIZATION_RELEASE TRUE
)
```

이후 문제가 없고 효과가 확인되면 다른 target으로 넓힙니다.

### 15-4. 외부 라이브러리와 toolchain을 확인한다

정적 라이브러리도 LTO 효과를 보려면 같은 계열의 toolchain과 LTO 호환 방식으로 빌드되어야 합니다.

확인할 항목은 아래와 같습니다.

- 컴파일러 버전
- 링커 종류와 버전
- archiver, ranlib의 LTO plugin 지원
- 정적 라이브러리의 LTO 정보 포함 여부
- prebuilt library의 컴파일러 호환성
- cross compile toolchain 파일의 설정

### 15-5. 끄기 쉬운 옵션으로 만든다

LTO는 문제 분석 시 빠르게 끌 수 있어야 합니다.

```cmake
option(ENABLE_LTO "Enable link time optimization" OFF)

include(CheckIPOSupported)
check_ipo_supported(RESULT ipo_supported OUTPUT ipo_error)

if(ENABLE_LTO AND ipo_supported)
    set_property(TARGET my_app PROPERTY
        INTERPROCEDURAL_OPTIMIZATION_RELEASE TRUE
    )
elseif(ENABLE_LTO)
    message(WARNING "LTO requested but not supported: ${ipo_error}")
endif()
```

이렇게 해두면 CI나 로컬에서 비교하기 쉽습니다.

```bash
cmake -S . -B build-release -DCMAKE_BUILD_TYPE=Release -DENABLE_LTO=ON
cmake --build build-release
```

---

## 16. 자주 만나는 문제와 해결 방법

### undefined reference 또는 심볼 관련 오류가 난다

LTO를 켰을 때만 링크 오류가 난다면 toolchain 호환성, 정적 라이브러리 생성 방식, 심볼 visibility 설정을 확인해야 합니다.

특히 정적 라이브러리를 만들 때 LTO object를 제대로 다룰 수 있는 `ar`, `ranlib`이 사용되는지 확인해야 합니다.
GCC 계열에서는 `gcc-ar`, `gcc-ranlib`이 필요한 환경도 있습니다.

### 링크가 너무 느리다

full LTO 대신 ThinLTO를 검토합니다.
GCC라면 `-flto=auto` 또는 job 수 지정도 확인합니다.
또한 모든 target에 LTO를 켜지 말고 성능에 중요한 target에만 적용합니다.

### 메모리 부족으로 실패한다

LTO 병렬도를 낮추거나, ThinLTO를 사용하거나, target을 나누어 적용합니다.
CI runner의 메모리 상향도 현실적인 해결책입니다.

### 디버깅이 어렵다

Debug 빌드에서는 LTO를 끄고, `RelWithDebInfo`에서만 필요한 경우 제한적으로 사용합니다.
문제 재현용 빌드에서는 LTO ON/OFF를 쉽게 바꿀 수 있도록 해야 합니다.

### 성능이 오히려 나빠졌다

LTO가 항상 성능을 개선하는 것은 아닙니다.
인라이닝 증가로 코드 크기가 커지고 instruction cache 효율이 떨어질 수 있습니다.
프로파일 기반 최적화인 PGO와 함께 검토하거나, 특정 모듈에서만 LTO를 적용하는 방법을 고려합니다.

---

## 17. LTO와 PGO를 함께 쓰는 경우

LTO는 프로그램 구조를 넓게 보고 최적화합니다.
PGO(Profile Guided Optimization)는 실제 실행 프로파일을 보고 최적화합니다.

둘을 함께 쓰면 더 강력할 수 있습니다.

```text
LTO:
코드 구조를 넓게 봄

PGO:
실제 실행 빈도와 hot path를 봄
```

예를 들어 컴파일러가 어떤 함수를 인라이닝할지 결정할 때, LTO는 함수 경계를 넘는 정보를 제공하고 PGO는 실제로 자주 호출되는 경로를 알려줍니다.

다만 빌드 파이프라인은 더 복잡해집니다.

```text
1. instrumented build 생성
2. 대표 workload 실행
3. profile 수집
4. profile을 사용해 최적화 빌드 생성
5. 필요하면 LTO도 함께 적용
```

성능이 정말 중요한 제품이라면 LTO와 PGO 조합을 검토할 만하지만, 일반 프로젝트에서는 먼저 LTO 단독 효과부터 측정하는 편이 좋습니다.

---

## 18. LTO 적용 체크리스트

LTO를 적용하기 전에 아래 항목을 확인하면 시행착오를 줄일 수 있습니다.

- Release 빌드에서만 켜도록 설정했는가?
- LTO ON/OFF를 쉽게 바꿀 수 있는 옵션이 있는가?
- 컴파일 단계와 링크 단계에 일관되게 LTO 옵션이 들어가는가?
- CMake라면 `CheckIPOSupported`로 지원 여부를 확인했는가?
- 정적 라이브러리도 LTO 호환 방식으로 빌드되는가?
- 외부 prebuilt library와 toolchain 호환성을 확인했는가?
- 링크 시간과 peak memory를 측정했는가?
- 실행 파일 크기 변화를 측정했는가?
- 핵심 벤치마크 성능을 측정했는가?
- Debug 또는 빠른 로컬 개발 빌드에는 LTO가 꺼져 있는가?
- LTO를 끈 fallback release 빌드를 만들 수 있는가?
- CI에서 LTO 빌드를 어느 단계에 둘지 정했는가?

---

## 19. 결론

LTO는 C/C++ 프로젝트에서 최종 실행 파일을 더 잘 최적화하기 위한 강력한 빌드 옵션입니다.
전통적인 파일 단위 컴파일의 한계를 줄이고, 링크 단계에서 여러 object file을 함께 분석해 더 넓은 범위의 최적화를 수행합니다.

잘 맞는 프로젝트에서는 실행 성능이 좋아지고 바이너리 크기가 줄어들 수 있습니다.
작은 함수 호출이 많거나, 템플릿과 추상화 계층이 두꺼운 C++ 코드에서는 특히 효과를 볼 가능성이 있습니다.

하지만 공짜는 아닙니다.
링크 시간이 길어지고, 메모리를 더 쓰고, toolchain 호환성 문제가 생길 수 있으며, 디버깅과 문제 분석이 어려워질 수 있습니다.

그래서 LTO의 핵심은 "켜면 빨라진다"가 아니라 아래에 가깝습니다.

```text
Release 결과물의 성능과 크기를 개선할 가능성이 있다.
대신 링크 비용과 toolchain 복잡도를 지불해야 한다.
그러니 반드시 측정하고, 켜고 끄기 쉽게 관리해야 한다.
```

실무에서 가장 무난한 전략은 단순합니다.

```text
1. Debug 빌드에는 켜지 않는다.
2. Release 빌드에서 타겟 단위로 실험한다.
3. 성능, 크기, 링크 시간, 메모리를 측정한다.
4. 효과가 있는 target에만 적용한다.
5. 문제가 생기면 즉시 끌 수 있게 옵션화한다.
```

LTO는 빌드 옵션 하나로 끝나는 기능이라기보다, 컴파일러와 링커가 프로그램 전체를 더 깊게 이해하도록 만드는 최적화 전략입니다.
제대로 측정하고 관리하면 release 빌드 품질을 끌어올리는 좋은 도구가 될 수 있습니다.
