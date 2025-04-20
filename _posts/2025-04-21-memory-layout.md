---
title: "C에서 메모리 구조(stack/heap/static)를 시각적으로 이해하기"
date: 2025-04-20
cateogry: C
tags: [C, 메모리, 시스템프로그래밍, 스택, 힙, 정적 메모리]
---

# C에서 메모리 구조(stack/heap/static)를 시각적으로 이해하기

C 프로그램은 실행될 때 운영체제에 의해 여러 영역으로 나뉜 메모리를 사용합니다.  
이 메모리 구조를 잘 이해해야 **포인터**, **메모리 할당/해제**, **버그 원인 파악**에 능숙해질 수 있습니다.

---

## 📦 C 메모리 구조 요약

<img src='/assets/img/2025-04-21_memory.png' width=400>
> 위 구조는 프로세스 메모리 공간의 대표적인 구성입니다.

## 🔍 각 영역 설명

| 영역  | 설명                                         |
| ----- | -------------------------------------------- |
| Text  | 컴파일된 함수 코드가 저장됨 (읽기 전용)      |
| Data  | 초기값이 있는 전역/정적 변수                 |
| BSS   | 초기값이 없는 전역/정적 변수                 |
| Heap  | 런타임 중 malloc() 등으로 동적 할당          |
| Stack | 함수 호출 시 생성되는 지역 변수, 매개변수 등 |

## 🧪 실습 예제: 메모리 위치 출력

```c
#include <stdio.h>
#include <stdlib.h>

int global_var = 10;          // Data 영역
static int static_var;        // BSS 영역

int main() {
    int local_var = 5;        // Stack 영역
    int* heap_var = malloc(sizeof(int));  // Heap 영역
    *heap_var = 100;

    printf("코드 주소 (main):     %p\n", (void*)main);
    printf("전역 변수 주소:       %p\n", (void*)&global_var);
    printf("static 변수 주소:     %p\n", (void*)&static_var);
    printf("지역 변수 주소:       %p\n", (void*)&local_var);
    printf("힙 변수 주소:         %p\n", (void*)heap_var);

    free(heap_var);
    return 0;
}
```

## ▶️ 실행 결과 예시

```text
코드 주소 (main):     0x564d8a27e6d9
전역 변수 주소:       0x564d8a48104c
static 변수 주소:     0x564d8a481048
지역 변수 주소:       0x7ffc6a939e3c
힙 변수 주소:         0x564d8c0c8260
```

- main() 주소는 텍스트 영역

- 전역변수/정적변수는 Data/BSS

- local_var는 스택 (주소가 높음)

- heap_var는 힙 (주소가 낮음)

## 🧠 정리 포인트

- **지역 변수** → `Stack` 영역에 저장됨  
- **전역 변수** → 초기값이 있으면 `Data`, 없으면 `BSS`에 저장됨  
- **정적 변수 (`static`)** → 전역처럼 `Data/BSS` 영역에 저장되며 함수 외부에서도 유지됨  
- **동적 변수 (`malloc`)** → `Heap`에 저장되며 `free()`로 해제 필요  
- **함수/코드** → `Text` 영역 (읽기 전용)

> 💡 예시: 지역 변수의 주소를 반환하면 함수 종료 후 사라지기 때문에 위험! → **Dangling pointer**  
> 💡 `Heap` 메모리는 수동 해제가 필요하므로, 실수하면 **메모리 누수**가 발생함.

## ✅ 실무에서 유용한 팁

| 상황 | 유의사항                                        |
| ---- | ----------------------------------------------- |
| 지역 | 변수 포인터 리턴	❌ Stack 메모리 해제됨          |
| 동적 | 메모리 미해제	❌ 메모리 누수 발생                |
| 정적 | 변수	✅ 여러 함수에서 공유, but 주의해서 써야 함 |
