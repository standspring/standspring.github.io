---
title: "gdb로 C 메모리 구조 파악 및 core dump 분석하기"
date: 2025-04-22
category: C
tags: [C, gdb, 디버깅, 시스템프로그래밍, 메모리분석]
---

# gdb로 C 메모리 구조 분석하기 — 실습 중심 튜토리얼

C 언어를 사용하다 보면 어느 순간 마주하게 되는 `Segmentation Fault`, `버퍼 오버플로우`, `메모리 누수`.  
이럴 때 진짜 무기를 꺼내야죠 — 바로 `gdb`입니다.

이 글에서는 gdb로 **Stack / Heap / 전역 변수** 등을 **직접 추적하며 시각적으로 메모리를 분석**하는 방법을 단계별로 정리합니다.

---

## 🧪 분석 대상 코드

```c
#include <stdio.h>
#include <stdlib.h>

int global_var = 100;

void print_addrs() {
    int local_var = 42;
    int* heap_var = malloc(sizeof(int));
    *heap_var = 777;

    printf("[main] global_var addr : %p\n", (void*)&global_var);
    printf("[main] local_var addr  : %p\n", (void*)&local_var);
    printf("[main] heap_var addr   : %p\n", (void*)heap_var);

    free(heap_var);
}

int main() {
    print_addrs();
    return 0;
}
```

---

## ⚙️ 컴파일

```bash
gcc -g memtest.c -o memtest
```

> `-g` 옵션은 디버깅 심볼 정보를 포함시켜 gdb에서 소스 코드 수준 분석이 가능하게 해줍니다.

---

## 🧩 gdb로 분석 시작

```bash
gdb ./memtest
```

### 1. 브레이크포인트 설정

```gdb
(gdb) break print_addrs
```

### 2. 실행

```gdb
(gdb) run
```

### 3. 변수 주소 보기

```gdb
(gdb) print &global_var
(gdb) print &local_var
(gdb) print heap_var
```

---

## 🔍 메모리 위치로 영역 구분하기

| 변수         | 예상 영역            |
| ------------ | -------------------- |
| `global_var` | Data 또는 BSS (전역) |
| `local_var`  | Stack                |
| `heap_var`   | Heap                 |

예시 출력:

```text
$1 = (int *) 0x404024        ← global_var
$2 = (int *) 0x7fffffffe53c  ← local_var
$3 = (int *) 0x555555757260  ← heap_var
```

---

## 🧠 주소 비교로 이해하기

- `global_var`는 **고정된 낮은 주소 (0x400000번대)** → 실행 파일 내부 (data 영역)
- `local_var`는 **높은 주소 (0x7ffffff...)** → 스택
- `heap_var`는 중간 주소 (보통 0x55... 또는 0x60...대) → 힙

---

## 💡 메모리 안의 값도 확인 가능

```gdb
(gdb) x/4x &global_var     # 4개 정수(hex)로 보기
(gdb) x/4d &global_var     # 4개 정수(decimal)
```

또는

```gdb
(gdb) x/1i main            # main 함수의 첫 어셈블리 명령
```

---

## ⚠️ 실수 예제: 스택 변수 포인터 리턴

```c
int* bad_func() {
    int x = 999;
    return &x;  // 위험!
}
```

```gdb
(gdb) break bad_func
(gdb) run
(gdb) next
(gdb) print &x
```

→ 함수 종료 후 포인터를 쓰면, **이미 해제된 stack 주소 접근**이기 때문에 **segfault** 발생!

---

## ✅ 정리

| gdb 명령         | 설명                       |
| ---------------- | -------------------------- |
| `break func`     | 함수에 브레이크포인트 설정 |
| `run`            | 프로그램 실행              |
| `next` or `step` | 다음 줄 실행               |
| `print var`      | 변수 값 출력               |
| `x/4x addr`      | 메모리 주소 직접 확인      |
| `bt`             | 백트레이스(호출 스택 출력) |

---

# gdb에서 core dump 분석하기 — 크래시 원인 추적 실습

프로그램이 갑자기 종료되고 "Segmentation fault (core dumped)"라는 메시지를 본 적 있으신가요?  
이때 생성된 **core dump 파일은 프로그램이 죽던 그 순간의 메모리 상태를 저장한 스냅샷**입니다.

이 글에서는 `gdb`를 사용하여 core dump를 분석하고 **버그 원인을 추적하는 방법**을 알려드립니다.

---

## 🔧 core dump 생성 설정

리눅스에서는 기본적으로 core dump 생성을 제한하고 있습니다.  
아래 명령으로 core 파일이 생성되도록 설정하세요.

```bash
ulimit -c unlimited          # 현재 쉘에서 core dump 크기 제한 해제
echo "/tmp/core.%e.%p" | sudo tee /proc/sys/kernel/core_pattern
```

- `%e`: 실행 파일 이름  
- `%p`: 프로세스 ID  

> core 파일은 보통 `/tmp/` 또는 현재 디렉토리에 저장됩니다.

---

## 🧪 실습용 크래시 코드

```c
#include <stdio.h>

void crash() {
    int *p = NULL;
    *p = 42;  // Null pointer dereference
}

int main() {
    crash();
    return 0;
}
```

---

## ⚙️ 컴파일

```bash
gcc -g crash.c -o crash
```

> `-g` 옵션은 디버깅 정보를 포함시켜 gdb에서 분석 가능하게 해줍니다.

---

## 💥 실행 후 core 생성 확인

```bash
./crash
# Segmentation fault (core dumped)

ls /tmp/core.*
# → core.crash.12345
```

---

## 🔍 gdb로 core 파일 열기

```bash
gdb ./crash /tmp/core.crash.12345
```

이제 `gdb`가 프로그램이 죽은 지점의 메모리 상태를 불러와 분석할 수 있습니다.

---

## 🔎 주요 gdb 명령

```gdb
(gdb) bt              # 백트레이스 (호출 스택)
(gdb) info locals     # 지역 변수 상태 확인
(gdb) frame 0         # 현재 프레임으로 이동
(gdb) list            # 죽은 줄 근처 소스 보기
(gdb) print *p        # 원인 변수 출력
```

---

## ✅ 분석 예시 결과

```text
Program terminated with signal SIGSEGV, Segmentation fault.
#0  crash () at crash.c:5
5       *p = 42;
(gdb) bt
#0  crash () at crash.c:5
#1  0x0000000000401136 in main () at crash.c:9
```

---

## 💡 핵심 요약

- core 파일은 **죽던 그 순간의 메모리와 레지스터 정보를 저장**한 디버깅 자료입니다.
- 반드시 `-g` 옵션을 주고 컴파일해야 gdb에서 분석 가능합니다.
- `bt`, `info locals`, `print` 등을 통해 문제 코드 위치 및 상태를 파악할 수 있습니다.

---
