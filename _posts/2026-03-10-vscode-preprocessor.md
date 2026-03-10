---
title: "VS Code에서 C 전처리 지시자(`#ifdef`, `#if`) 임의로 컨트롤하는 방법"
date: 2026-03-10 00:00:00 +0900
categories: vscode
tags: [vscode, c, preprocessor]
toc: true
toc_sticky: true
---

C 개발을 하다 보면 `#ifdef`, `#if`, `#define` 같은 전처리 지시자를 자주 사용하게 됩니다.
특히 기능 테스트, 디버그 분기, 개발/배포 모드 전환 시 매우 유용합니다.

이번 글에서는 **VS Code에서 전처리 지시자를 쉽게 제어하는 방법**을 정리합니다. 🚀

---

## 1. 가장 기본: 코드 안에서 직접 `#define` 제어

가장 단순한 방법은 코드 내부에서 직접 매크로를 선언하는 것입니다.

```c
#define FEATURE_A

#ifdef FEATURE_A
printf("A enabled\n");
#else
printf("A disabled\n");
#endif
```

### 비활성화

```c
// #define FEATURE_A
```

이 방법은 바로 이해하기 쉽지만,
기능을 바꿀 때마다 소스를 수정해야 하므로 규모가 커질수록 불편합니다.

---

## 2. VS Code에서 `c_cpp_properties.json`으로 제어

VS Code에서는 `.vscode/c_cpp_properties.json` 파일을 이용해
IntelliSense 기준 매크로를 지정할 수 있습니다.

### 폴더 구조

```text
project/
 ├─ main.c
 └─ .vscode/
      └─ c_cpp_properties.json
```

### 설정 파일 작성

```json
{
  "configurations": [
    {
      "name": "Win32",
      "includePath": [
        "${workspaceFolder}/**"
      ],
      "defines": [
        "FEATURE_A",
        "DEBUG"
      ],
      "compilerPath": "C:/mingw64/bin/gcc.exe",
      "cStandard": "c17",
      "intelliSenseMode": "windows-gcc-x64"
    }
  ],
  "version": 4
}
```

### 동작 확인

```c
#ifdef FEATURE_A
printf("A ON");
#else
printf("A OFF");
#endif
```

`defines`에서 `"FEATURE_A"`를 제거하면
VS Code에서 해당 영역이 회색으로 비활성 표시됩니다.

즉:

* IntelliSense 즉시 반영
* inactive code 시각화 가능

---

## 3. inactive code 회색 표시 활성화

VS Code 설정에서 아래 옵션을 켜면 비활성 코드가 더 잘 보입니다.

```json
"C_Cpp.dimInactiveRegions": true
```

---

## 4. 실제 컴파일 시 매크로 전달 (`gcc -D`)

`c_cpp_properties.json`은 편집기 표시용입니다.
실제 컴파일에는 `-D` 옵션을 사용해야 합니다.

### 컴파일 예시

```bash
gcc main.c -DFEATURE_A -o main.exe
```

### 코드

```c
#ifdef FEATURE_A
printf("enabled\n");
#endif
```

### 값 전달도 가능

```bash
gcc main.c -DVERSION=2
```

```c
#if VERSION == 2
printf("version2\n");
#endif
```

---

## 5. 가장 추천: `config.h`로 즉시 토글

실무에서는 별도 설정 파일을 두는 방식이 가장 많이 사용됩니다.

### config.h

```c
#define FEATURE_A 1
#define FEATURE_B 0
#define DEBUG_MODE 1
```

### main.c

```c
#include "config.h"

#if FEATURE_A
printf("A ON\n");
#endif

#if DEBUG_MODE
printf("debug log\n");
#endif
```

### 토글

```c
#define FEATURE_A 0
```

숫자만 바꾸면 바로 전환됩니다.

---

## 6. `#if 0` 임시 비활성화

특정 코드 블록을 잠시 막고 싶을 때 가장 빠른 방법입니다.

```c
#if 0
printf("임시 중지");
#endif
```

### 다시 활성화

```c
#if 1
printf("다시 활성화");
#endif
```

---

## 7. 추천 프로젝트 구조

```text
project/
 ├─ main.c
 ├─ config.h
 └─ .vscode/
      └─ c_cpp_properties.json
```

이 구조를 쓰면:

* IntelliSense 제어
* 빌드 분기
* 기능 토글

모두 깔끔하게 관리됩니다.

---

## 정리

추천 우선순위:

1. `config.h`로 기능 토글
2. `c_cpp_properties.json`으로 IntelliSense 제어
3. `gcc -D`로 빌드 분기

---
