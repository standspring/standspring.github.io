---
title: "valgrind 사용법과 메모리 누수 잡기 — 실습 가이드"
date: 2025-04-27
category: C
tags: [C, valgrind, 디버깅, 메모리누수, 시스템프로그래밍]
---

# valgrind 사용법과 메모리 누수 잡기 — 실습 가이드

C 프로그램을 작성할 때 가장 흔한 실수 중 하나는 **메모리 누수(memory leak)**입니다.  
이 문제를 자동으로 찾아주는 강력한 도구가 바로 `valgrind`입니다.

이번 글에서는 **valgrind 사용법**과 **메모리 누수 예제 분석**을 실습 중심으로 다룹니다.

---

## 🔧 valgrind 설치

Ubuntu / Debian 계열에서는 다음 명령어로 설치할 수 있습니다.

```bash
sudo apt update
sudo apt install valgrind
```

---

## 🧪 누수 발생 예제 코드

```c
#include <stdlib.h>

void leak() {
    int *p = malloc(sizeof(int) * 10);  // 메모리 할당
    p[0] = 42;                          // 사용
    // free(p);  // 해제를 깜빡!
}

int main() {
    leak();
    return 0;
}
```

---

## ⚙️ 컴파일

디버깅 정보를 포함하기 위해 `-g` 옵션을 추가합니다.

```bash
gcc -g leak.c -o leak
```

---

## 🛠️ valgrind로 실행

```bash
valgrind ./leak
```

기본 사용 방법입니다. 조금 더 자세한 보고를 위해서는 다음과 같이 실행할 수도 있습니다.

```bash
valgrind --leak-check=full --track-origins=yes ./leak
```

---

## 📋 예시 출력

```text
==12345== 40 bytes in 1 blocks are definitely lost in loss record 1 of 1
==12345==    at 0x4C2B0E3: malloc (vg_replace_malloc.c:299)
==12345==    by 0x40054A: leak (leak.c:5)
==12345==    by 0x40055D: main (leak.c:11)
```

- `definitely lost`: 프로그램이 종료될 때 참조할 수 없는 메모리 블록이 존재함
- `leak.c:5`: 문제 발생 위치 명시
- `malloc`, `leak`, `main` 함수 순서까지 추적 가능

---

## ✅ 메모리 누수 수정

문제 해결을 위해 `free(p);`를 추가합니다.

```c
void leak() {
    int *p = malloc(sizeof(int) * 10);
    p[0] = 42;
    free(p);  // 누수 방지
}
```

수정 후 다시 valgrind를 돌리면, 누수 관련 경고가 사라집니다.

---

## 🧠 추가 옵션들

| 옵션                      | 설명                           |
| ------------------------- | ------------------------------ |
| `--leak-check=full`       | 모든 메모리 누수 상세 보고     |
| `--track-origins=yes`     | 초기화되지 않은 값의 기원 추적 |
| `--show-leak-kinds=all`   | 다양한 누수 종류 출력          |
| `--log-file=valgrind.log` | 결과를 파일로 저장             |

---

# valgrind로 초기화되지 않은 메모리 접근 탐지하기

메모리를 할당한 후 초기화를 깜빡하면, 프로그램은 예측할 수 없는 값을 읽거나 이상 동작을 할 수 있습니다.  
이런 버그를 찾아내는 데도 `valgrind`는 아주 유용한 도구입니다.

이번 글에서는 **초기화되지 않은 메모리를 사용하는 코드**를 실험하고,  
`valgrind`로 어떻게 탐지하는지 실습해봅니다.

---

## 🧪 문제 코드 예제

```c
#include <stdio.h>
#include <stdlib.h>

int main() {
    int *p = malloc(sizeof(int) * 5);  // 메모리 할당
    printf("값: %d\n", p[2]);         // 초기화하지 않고 사용
    free(p);
    return 0;
}
```

- `p[2]`는 초기화되지 않은 상태입니다.
- 읽는 시점에 쓰레기값이 출력될 수 있으며, 시스템에 따라 다르게 동작할 수 있습니다.

---

## ⚙️ 컴파일

디버깅 정보를 추가합니다.

```bash
gcc -g uninit.c -o uninit
```

---

## 🛠️ valgrind로 실행

```bash
valgrind --track-origins=yes ./uninit
```

---

## 📋 예시 출력

```text
==12345== Conditional jump or move depends on uninitialised value(s)
==12345==    at 0x4005B3: main (uninit.c:7)
==12345==  Uninitialised value was created by a heap allocation
==12345==    at 0x4C2B0E3: malloc (vg_replace_malloc.c:299)
==12345==    by 0x4005A6: main (uninit.c:6)
```

- "Conditional jump or move depends on uninitialised value(s)" 라는 메시지가 출력됩니다.
- `main()` 함수의 7번째 줄 (`printf`)에서 초기화되지 않은 값을 사용했다고 추적합니다.

---

## ✅ 문제 수정

배열을 사용하기 전에 반드시 초기화합니다.

```c
int main() {
    int *p = malloc(sizeof(int) * 5);
    for (int i = 0; i < 5; i++) {
        p[i] = 0;  // 초기화
    }
    printf("값: %d\n", p[2]);
    free(p);
    return 0;
}
```

또는, `calloc()`을 사용해 메모리를 0으로 초기화할 수도 있습니다.

```c
int *p = calloc(5, sizeof(int));
```

---

# 실전 프로젝트 예제 — valgrind로 메모리 누수와 초기화 오류 모두 잡기

실제 프로젝트에서는 메모리 누수(memory leak)와 초기화되지 않은 메모리 사용(uninitialized memory)이 함께 발생하는 경우가 많습니다.  
이번 글에서는 **복합적인 오류가 포함된 작은 프로젝트 코드**를 분석하고,  
`valgrind`를 이용해 문제를 모두 찾아내는 방법을 실습합니다.

---

## 🧪 실습용 코드 예제

```c
#include <stdio.h>
#include <stdlib.h>

typedef struct {
    int id;
    char *name;
} Person;

Person* create_person(int id) {
    Person *p = malloc(sizeof(Person));
    p->id = id;
    // p->name 초기화 안함
    return p;
}

int main() {
    Person *john = create_person(1);

    printf("ID: %d\n", john->id);
    printf("Name: %s\n", john->name); // 초기화되지 않은 메모리 접근

    // free(john);  // 메모리 해제 깜빡!

    return 0;
}
```

---

## ⚙️ 컴파일

```bash
gcc -g project.c -o project
```

---

## 🛠️ valgrind로 실행

```bash
valgrind --leak-check=full --track-origins=yes ./project
```

---

## 📋 예시 출력 분석

```text
==12345== Conditional jump or move depends on uninitialised value(s)
==12345==    at 0x4E7F13: puts (iofputs.c:32)
==12345==    by 0x4005B2: main (project.c:21)

==12345== 24 bytes in 1 blocks are definitely lost in loss record 1 of 1
==12345==    at 0x4C2B0E3: malloc (vg_replace_malloc.c:299)
==12345==    by 0x40059D: create_person (project.c:11)
==12345==    by 0x4005AD: main (project.c:18)
```

- **초기화되지 않은 메모리 사용**: `john->name` 출력 시 발생
- **메모리 누수**: `Person` 구조체를 할당했지만 `free` 하지 않음

---

## ✅ 문제 수정

1. `name`을 NULL로 초기화하거나 적절한 값을 설정합니다.
2. 프로그램 종료 전에 할당된 메모리를 해제합니다.

수정된 코드:

```c
Person* create_person(int id) {
    Person *p = malloc(sizeof(Person));
    p->id = id;
    p->name = NULL; // 초기화
    return p;
}

int main() {
    Person *john = create_person(1);

    printf("ID: %d\n", john->id);
    if (john->name)
        printf("Name: %s\n", john->name);
    else
        printf("Name: (없음)\n");

    free(john);
    return 0;
}
```

---

## 🧠 실전 디버깅 요령

| 상황                       | 대처법                          |
| -------------------------- | ------------------------------- |
| malloc 후 초기화 안함      | `memset` 또는 명시적 초기화     |
| 구조체 포인터 free 깜빡    | 함수 종료 직전 명시적 free 호출 |
| 출력 전에 포인터 NULL 체크 | `if (ptr)` 로 가드              |

---
