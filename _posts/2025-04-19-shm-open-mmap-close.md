---
title: "shm_open, mmap, close의 관계 정리"
date: 2025-04-19
category: C
tags: [C, 시스템프로그래밍, 공유메모리, shm_open, mmap]
---

# `shm_open`, `mmap`, `close`의 관계 정리  
> POSIX 공유 메모리에서 자주 헷갈리는 부분을 C 코드 예제와 함께 이해하기

공유 메모리(`shm_open`, `mmap`)를 처음 사용할 때 가장 많이 나오는 질문 중 하나:

> "`shm_open`으로 파일 디스크립터를 열고 `mmap`으로 매핑했는데, `close`를 해도 괜찮을까?"

이 글에서는 그 질문에 명확히 답하고, 공유 메모리 사용 시의 메모리 흐름을 단계별로 설명합니다.

---

## 1. 기본 흐름

1. `shm_open()` — 공유 메모리 객체(가상 파일)를 엽니다.  
2. `ftruncate()` — 공유 메모리 크기를 설정합니다.  
3. `mmap()` — 해당 객체를 가상 메모리에 매핑합니다.  
4. `close()` — 파일 디스크립터를 닫습니다. **(여기서 혼동 많음)**  
5. `munmap()` — 매핑 해제  
6. `shm_unlink()` — 공유 메모리 객체 삭제  

---

## 2. 각 함수의 역할 정리

| 함수         | 역할                                           |
| ------------ | ---------------------------------------------- |
| `shm_open`   | 공유 메모리 객체(파일 디스크립터) 생성 및 열기 |
| `ftruncate`  | 공유 메모리의 크기를 설정                      |
| `mmap`       | 메모리 주소 공간에 공유 메모리 매핑            |
| `close`      | 파일 디스크립터 닫기 (매핑은 유지됨)           |
| `munmap`     | 매핑된 메모리 해제                             |
| `shm_unlink` | 공유 메모리 파일 시스템에서 제거               |

---

## 3. `mmap()` 이후, `close()` 해도 되는가?

### ✅ 결론: **된다.**

`mmap()`으로 매핑을 완료했다면, 해당 파일 디스크립터를 `close()`해도 공유 메모리 자체에는 **영향 없음**.

- `close(fd)`는 단순히 **파일 디스크립터를 닫는 것**일 뿐,  
- `mmap()`으로 매핑된 메모리 공간은 여전히 **유효**합니다.  
- 작업이 끝난 후 `munmap()`으로 해제하면 됩니다.

> 단, 아직 `mmap()`을 하지 않았을 경우에는 `close()` 하지 마세요. 매핑 전에 닫아버리면 매핑 자체가 불가능해집니다.

---

### close(fd) 하지 않은 경우
fd가 열린 상태로 유지됩니다.

공유 메모리 객체가 참조 중이라 shm_unlink()를 호출해도 실제 삭제는 지연됩니다.

프로세스 종료 시 커널이 FD를 정리하지만, FD 리소스 누수(FD leak) 가능성이 있습니다.

mmap()된 메모리는 정상적으로 접근할 수 있습니다.

### close(fd) 한 경우
파일 디스크립터가 정리되어 리소스 누수가 없습니다.

mmap()된 메모리는 여전히 접근 가능합니다.

munmap()으로 메모리 해제 후, shm_unlink()를 호출하면 공유 메모리 객체가 완전히 삭제됩니다 (다른 프로세스가 열고 있지 않은 경우).

### 
mmap() 이후에는 FD가 필요 없기 때문에 close(fd) 해도 문제가 없습니다.

mmap()된 메모리는 FD 없이도 사용 가능하므로 close()는 자원 정리 차원에서 권장됩니다.

깔끔한 자원 정리를 위해 다음과 같은 순서를 따르세요:

```c
close(fd);
munmap(addr, size);
shm_unlink("/my_shm");
```

## 📊 차이 요약

| 항목                             | `close()` 하지 않음                      | `close()` 호출함                                 |
| -------------------------------- | ---------------------------------------- | ------------------------------------------------ |
| 메모리 접근 가능 여부            | ✅ 가능                                   | ✅ 가능                                           |
| FD 리소스 정리 여부              | ❌ 안 됨 (FD leak 위험)                   | ✅ 정리됨                                         |
| `shm_unlink()` 후 삭제 가능 여부 | ❌ 지연됨 (FD가 열려 있어 즉시 삭제 불가) | ✅ 가능 (다른 프로세스가 열지 않았다면 즉시 삭제) |
| 프로세스 종료 시 자동 정리 여부  | ✅ 커널에 의해 정리되지만 명시적이지 않음 | ✅ 명시적으로 정리됨                              |
| 권장 여부                        | ⚠️ 비권장                                 | ✅ **권장**                                       |


## 4. 예제 코드

```c
#include <fcntl.h>
#include <sys/mman.h>
#include <unistd.h>
#include <stdio.h>
#include <string.h>

int main() {
    const char* name = "/my_shm";
    const size_t size = 4096;

    int fd = shm_open(name, O_CREAT | O_RDWR, 0666);
    ftruncate(fd, size);

    void* addr = mmap(NULL, size, PROT_READ | PROT_WRITE, MAP_SHARED, fd, 0);

    close(fd); // 여기서 닫아도 매핑된 addr는 유효함

    strcpy((char*)addr, "공유 메모리 테스트!");

    printf("메모리 내용: %s\n", (char*)addr);

    munmap(addr, size);
    shm_unlink(name);

    return 0;
}
```
