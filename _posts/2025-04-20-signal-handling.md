---
title: "signal 핸들링과 trap — C에서 프로세스를 안전하게 제어하기"
date: 2025-04-20
category: C
tags: [C, 시스템프로그래밍, signal, sigaction, trap, 리눅스]
---

# `signal` 핸들링과 `trap` — C에서 프로세스를 안전하게 제어하기

리눅스에서 실행 중인 프로세스는 다양한 "신호(Signal)"를 받을 수 있습니다.  
사용자가 `Ctrl+C`를 눌렀을 때, 또는 잘못된 메모리에 접근했을 때 발생하는 이 신호들을  
**적절히 핸들링(handle)** 하면, 프로그램이 **갑작스레 종료되는 상황을 막고**,  
**로그 저장**, **자원 해제** 같은 마무리 작업도 수행할 수 있습니다.

---

## 📌 Signal이란?

Signal은 운영체제가 프로세스에 전달하는 **비동기 이벤트 알림 메커니즘**입니다.  
다음은 자주 사용되는 시그널 예시입니다:

| Signal    | 의미                          | 기본 동작        |
| --------- | ----------------------------- | ---------------- |
| `SIGINT`  | 인터럽트 (`Ctrl+C`)           | 종료             |
| `SIGTERM` | 종료 요청 (`kill`)            | 종료             |
| `SIGKILL` | 강제 종료 (`kill -9`)         | 종료 (무시 불가) |
| `SIGSEGV` | 잘못된 메모리 접근 (세그폴트) | 종료             |
| `SIGCHLD` | 자식 프로세스 종료 알림       | 무시             |

---

## 🛠 signal() 함수로 간단한 핸들러 구현

```c
#include <stdio.h>
#include <signal.h>
#include <unistd.h>

void handle_sigint(int sig) {
    printf("\n[!] SIGINT 수신 (Ctrl+C)\n");
}

int main() {
    signal(SIGINT, handle_sigint);  // SIGINT가 발생하면 handle_sigint 실행

    while (1) {
        printf("작동 중...\n");
        sleep(1);
    }

    return 0;
}
```
이 코드는 Ctrl+C를 눌러도 프로그램이 종료되지 않고, 대신 "SIGINT 수신" 메시지를 출력합니다.

## 🧠 sigaction()을 이용한 고급 핸들링
signal()은 간단하지만 일부 시그널에서 안정성이 떨어질 수 있습니다.
보다 강력하고 유연한 시그널 처리를 위해선 sigaction()을 사용하는 것이 좋습니다.

```c
#include <stdio.h>
#include <signal.h>
#include <string.h>
#include <unistd.h>

void handler(int sig) {
    printf("[!] 시그널 %d 수신\n", sig);
}

int main() {
    struct sigaction sa;
    memset(&sa, 0, sizeof(sa));
    sa.sa_handler = handler;
    sigaction(SIGTERM, &sa, NULL);
    sigaction(SIGINT, &sa, NULL);

    while (1) {
        printf("대기 중...\n");
        sleep(2);
    }

    return 0;
}
```

### `sigaction()`에서 `siginfo_t`로 시그널 상세 정보 받기

일반적인 `signal()` 함수는 시그널 번호(`int sig`)만 받아서 처리합니다.  
하지만 보다 정밀한 시그널 정보를 얻고 싶다면 `sigaction()`을 사용하고,  
`sa_sigaction` 핸들러를 통해 `siginfo_t` 구조체를 받아야 합니다.

이를 통해 다음과 같은 정보를 확인할 수 있습니다:

- 누가 보낸 시그널인지 (PID)
- 어떤 코드(`SI_USER`, `SI_KERNEL`, 등)로 발생했는지
- 어떤 메모리 주소에서 오류가 났는지 (SIGSEGV 등)

---

### ✅ 핵심 구조: `sigaction`과 `siginfo_t`

```c
struct sigaction {
    void     (*sa_handler)(int);
    void     (*sa_sigaction)(int, siginfo_t *, void *);
    sigset_t   sa_mask;
    int        sa_flags;
};
```

sighandler 대신 sa_sigaction을 사용하려면 sa_flags에 SA_SIGINFO를 설정해야 합니다.

### 🧪 예제: SIGUSR1을 받았을 때 상세 정보 출력

```c
#include <stdio.h>
#include <signal.h>
#include <string.h>
#include <unistd.h>

void detailed_handler(int sig, siginfo_t *info, void *context) {
    printf("[시그널 수신] sig = %d\n", sig);
    printf("  → 보낸 PID: %d\n", info->si_pid);
    printf("  → 시그널 코드: %d\n", info->si_code);
}

int main() {
    struct sigaction sa;
    memset(&sa, 0, sizeof(sa));
    sa.sa_sigaction = detailed_handler;
    sa.sa_flags = SA_SIGINFO;

    sigaction(SIGUSR1, &sa, NULL);

    printf("PID: %d, SIGUSR1 수신 대기 중...\n", getpid());

    while (1) {
        pause(); // 시그널 대기
    }

    return 0;
}
```

### ▶️ 실행 & 테스트
1. 터미널 1에서 실행:

```bash
$ gcc siginfo.c -o siginfo
$ ./siginfo
PID: 12345, SIGUSR1 수신 대기 중...
```

2. 터미널 2에서 시그널 전송:

```bash
$ kill -USR1 12345
```

3.출력 결과:

```yaml
[시그널 수신] sig = 10
  → 보낸 PID: 54321
  → 시그널 코드: 0
```

### 🔍 siginfo_t로 알 수 있는 것들

| 필드      | 의미                                |
| --------- | ----------------------------------- |
| si_signo  | 시그널 번호                         |
| si_pid    | 시그널을 보낸 프로세스 ID           |
| si_uid    | 보낸 사용자 ID                      |
| si_code   | 시그널 발생 원인 코드               |
| si_addr   | (SIGSEGV 등에서) 접근한 주소        |
| si_status | 자식 프로세스의 종료 상태 (SIGCHLD) |

si_code가 SI_USER이면 일반 프로세스가 보낸 것이고,
SI_KERNEL이면 커널에 의해 발생된 시그널입니다.

### 🧠 언제 유용할까?

- 디버깅 SIGSEGV: 어떤 주소에 접근하다 오류가 났는지 확인

- 자식 종료 시 정보 확인(SIGCHLD): 어떤 자식이 어떤 상태로 종료됐는지 알 수 있음

- 로그 분석 및 감사(Audit): 누가 어떤 시그널을 보냈는지 기록 가능


## ⚠️ trap? 그거 셸에서 쓰는 거 아니야?
맞아요! trap은 Shell Script에서 시그널을 감지하고 특정 동작을 수행하게 하는 명령어입니다.

```bash
#!/bin/bash

trap 'echo "Ctrl+C 막음!"' INT

while true; do
    echo "실행 중..."
    sleep 1
done
```

이렇게 하면 사용자가 Ctrl+C를 눌러도 "Ctrl+C 막음!"이라는 메시지가 출력되고 종료되지 않죠.


## ✅ 결론 정리

| 개념 | C 코드 | 쉘 스크립트 |
| Signal           | 의미                  | 기본 동작        |
| ---------------- | --------------------- | ---------------- |
| 시그널 처리      | signal(), sigaction() | trap             |
| 비동기 이벤트    | ✔️                     | ✔️                |
| 자원 정리용 활용 | ✔️ (파일, 메모리)      | ✔️ (로그, 메시지) |

- 간단하게는 signal(), 확실하게는 sigaction()을 사용하세요.

- SIGINT, SIGTERM 같은 종료 시그널은 핸들링해서 깔끔한 마무리를 할 수 있습니다.

- 쉘 스크립트에서도 trap을 사용해 자동 종료 방지, 로그 처리 등을 구현할 수 있습니다.

- signal()은 간단하지만, sigaction() + siginfo_t 조합이 훨씬 강력합니다.

- 커널이 전달하는 시그널에 대한 정확한 원인과 메타 정보를 얻을 수 있습니다.

- 리눅스 시스템 프로그래밍이나 서버 프로세스의 안정성을 높이기 위해 필수적으로 알아야 할 개념입니다.
