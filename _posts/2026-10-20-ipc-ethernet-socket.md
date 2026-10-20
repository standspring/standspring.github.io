---
title: "IPC 패킷·이더넷 패킷·소켓 통신 비교: 프로세스에서 네트워크까지"
description: "IPC, 유닉스 도메인 소켓, TCP·UDP, IP 패킷과 이더넷 프레임의 관계를 계층별로 비교하고, 메시지 경계·MTU·MAC 주소·Python 소켓 예제와 디버깅 방법까지 정리합니다."
date: 2026-10-20 00:00:00 +0900
categories: [Development, Network]
tags: [IPC, Socket, Ethernet, TCP, UDP, Linux, Network, Python]
toc: true
toc_sticky: true
---

# IPC 패킷·이더넷 패킷·소켓 통신 비교: 프로세스에서 네트워크까지

## 들어가며

프로그램 사이에서 데이터를 주고받다 보면 “IPC 패킷을 보낸다”, “소켓으로 통신한다”, “eth 패킷을 캡처한다”라는 표현을 만난다. 모두 데이터 전달과 관련 있지만, 각각 가리키는 대상은 다르다.

**IPC는 프로세스 간 통신이라는 목적과 범주, 소켓은 통신에 사용하는 운영체제 인터페이스, 이더넷 프레임은 링크에서 전달하는 데이터 단위**다. TCP·UDP와 IP는 그 사이에서 서로 다른 역할을 맡는다.

![같은 호스트의 유닉스 도메인 소켓 IPC 경로와 다른 호스트로 향하는 TCP·IP·이더넷 경로, 그리고 계층별 데이터 포함 관계를 비교한 그림](/assets/img/2026-10-20-ipc-ethernet-socket.svg)

*로컬 IPC와 원격 네트워크 통신을 비교한 개념도다. 애플리케이션 메시지 하나와 TCP 세그먼트·이더넷 프레임 하나가 반드시 대응하는 것은 아니다.*

이 글은 Linux의 통신 구조를 중심으로 설명한다. Python TCP 예제는 Windows·Linux·macOS에서 실행할 수 있고, `AF_UNIX`, `AF_PACKET`의 세부 동작과 진단 명령어는 운영체제에 따라 차이가 있다.

## 문제 상황

다음 증상은 네트워크가 불안정하지 않아도 발생할 수 있다.

- 송신자가 두 번 `send()`했는데 수신자는 한 번에 두 메시지를 읽는다.
- `recv(1024)`를 호출했는데 1024바이트보다 적게 들어온다.
- 같은 컴퓨터에서 소켓 통신은 잘되지만 물리 네트워크 인터페이스에서는 패킷이 보이지 않는다.
- MTU가 1500인데 1500바이트짜리 UDP 본문을 보낼 때 문제가 생긴다.
- `sendall()`이 성공했는데 상대 프로그램이 요청을 처리했는지 알 수 없다.

이 문제를 풀려면 **애플리케이션이 정의하는 메시지, 소켓이 제공하는 전달 방식, 네트워크의 전송 단위**를 나누어 살펴봐야 한다.

## 원인 분석

### 1. IPC 패킷에는 공통된 표준 헤더가 있을까?

IPC는 **Inter-Process Communication**, 즉 프로세스 간 통신이다. 별도 주소 공간에서 실행되는 프로세스가 데이터를 교환하거나 실행 순서를 맞추는 방법을 말한다. 운영체제 프로그래밍에서는 주로 같은 호스트의 프로세스 사이 통신을 가리킨다. 분산 시스템 문맥에서는 원격 프로세스 간 통신까지 넓게 표현하기도 한다.

IPC 전체에 공통으로 적용되는 “IPC 패킷 헤더”는 없다. 다음처럼 전달 방식부터 다르다.

| IPC 방법 | 데이터를 전달하는 방식 | 메시지 경계 | 주로 쓰는 상황 |
|---|---|---|---|
| 파이프·FIFO | 커널이 관리하는 바이트 스트림 | 기본적으로 없음 | 명령어 연결, 단순한 데이터 파이프라인 |
| POSIX 메시지 큐 | 큐에 메시지를 넣고 꺼냄 | 있음 | 메시지 단위 작업 전달 |
| 공유 메모리 | 여러 프로세스가 같은 메모리 영역에 접근 | 직접 정의 | 큰 버퍼를 반복해서 공유 |
| 유닉스 도메인 소켓 | 로컬 소켓을 통해 데이터 교환 | 소켓 타입에 따라 다름 | 데몬 제어, 로컬 요청·응답 |

파이프의 작은 쓰기가 다른 쓰기와 섞이지 않는 **원자성**과, 읽을 때 메시지 경계를 유지하는 성질은 다르다. 일반적인 파이프·FIFO는 바이트 스트림이다. POSIX 메시지 큐는 메시지 단위 교환을 제공하며, 공유 메모리는 동기화 수단을 함께 설계해야 한다. ([pipe(7)](https://man7.org/linux/man-pages/man7/pipe.7.html), [mq_overview(7)](https://man7.org/linux/man-pages/man7/mq_overview.7.html), [shm_overview(7)](https://man7.org/linux/man-pages/man7/shm_overview.7.html))

실무에서 “IPC 패킷”이라고 부르는 것은 대개 다음처럼 **해당 프로그램이 약속한 메시지 형식**이다.

```text
[본문 길이][메시지 종류][요청 ID][본문]
```

이 형식을 유닉스 도메인 소켓에 실을 수도 있고, TCP에 실을 수도 있다. 공유 메모리의 슬롯에 저장할 수도 있다. 따라서 IPC 패킷이라는 말을 들으면 먼저 **어떤 전송 수단을 쓰며, 메시지 경계와 필드를 누가 정의하는지** 확인해야 한다.

### 2. 소켓은 TCP와 같은 뜻일까?

소켓은 프로그램이 운영체제의 통신 기능을 이용하는 **통신 종단점(endpoint)**이다. Linux에서 소켓을 만들면 파일 디스크립터를 돌려받고, `bind()`, `connect()`, `send()`, `recv()` 같은 API로 다룬다.

소켓을 생성할 때는 주소 체계와 전달 방식을 선택한다. 같은 `SOCK_STREAM`이라도 주소 체계가 다르면 통신 경로가 달라진다. ([socket(2)](https://man7.org/linux/man-pages/man2/socket.2.html))

| 주소 체계와 타입 | 일반적인 의미 | 상대를 식별하는 기준 |
|---|---|---|
| `AF_UNIX` + `SOCK_STREAM` | 로컬 바이트 스트림 | 소켓 경로명 등 |
| `AF_UNIX` + `SOCK_DGRAM` | 로컬 메시지 단위 통신 | 소켓 경로명 등 |
| `AF_UNIX` + `SOCK_SEQPACKET` | 연결을 맺고 순서·메시지 경계 유지 | 소켓 경로명 등 |
| `AF_INET` / `AF_INET6` + `SOCK_STREAM` | 일반적인 TCP 통신 | IPv4 / IPv6 주소와 포트 |
| `AF_INET` / `AF_INET6` + `SOCK_DGRAM` | 일반적인 UDP 통신 | IPv4 / IPv6 주소와 포트 |
| `AF_PACKET` + `SOCK_RAW` | Linux의 링크 계층 프레임 접근 | 인터페이스·링크 계층 주소 등 |

유닉스 도메인 소켓은 **소켓을 이용한 IPC 방법**이다. “IPC와 소켓 중 무엇을 쓸까?”보다 “로컬 IPC에 파이프, 공유 메모리, 유닉스 도메인 소켓 중 무엇이 맞을까?”라고 비교하는 편이 정확하다.

`/run/example.sock` 같은 경로명은 소켓을 찾기 위한 이름이다. 본문을 그 파일에 저장했다가 읽는 방식이 아니다. Linux에는 파일시스템 경로를 사용하지 않는 abstract namespace도 있다. ([unix(7)](https://man7.org/linux/man-pages/man7/unix.7.html))

`AF_PACKET`은 일반적인 TCP 소켓과 사용 목적이 다르다. 링크 계층 헤더에 접근하는 패킷 도구 등에 쓰이며, Linux에서는 생성 시 관련 사용자 네임스페이스의 `CAP_NET_RAW` 권한이 필요하다. `AF_INET`의 raw socket과도 구분해야 한다. ([packet(7)](https://man7.org/linux/man-pages/man7/packet.7.html))

### 3. 같은 소켓 API를 써도 데이터가 지나는 길은 다르다

**유닉스 도메인 소켓으로 같은 호스트에서 통신할 때**의 개념적 경로는 다음과 같다.

```text
프로세스 A → 로컬 소켓 → 운영체제 커널 → 로컬 소켓 → 프로세스 B
```

이 경로에 TCP·IP 헤더나 이더넷 프레임은 필요하지 않다.

**같은 호스트에서 `127.0.0.1` 또는 `::1`로 TCP 통신할 때**는 다르다.

```text
프로세스 A → TCP/IP → 루프백 경로 → TCP/IP → 프로세스 B
```

IP 주소·포트와 TCP 동작을 사용하지만, 일반적인 루프백 통신은 외부 물리 NIC로 나가지 않는다. 따라서 TCP로 통신한다고 물리 이더넷 프레임이 반드시 선로에 흐르는 것은 아니다.

**다른 호스트로 이더넷을 통해 TCP 통신할 때**는 다음과 같은 계층을 거친다.

```text
애플리케이션 메시지
    ↓ 소켓 API에 바이트 전달
TCP 바이트 스트림 → TCP 세그먼트
    ↓
IP 패킷
    ↓
이더넷 프레임 → NIC → 스위치·라우터 등 → 상대 호스트
```

수신 측은 반대 방향으로 처리한다. 이 과정에서 IP는 네트워크 사이의 전달을 맡고, TCP는 애플리케이션에 순서가 있는 바이트 스트림을 제공한다. Wi-Fi 등 다른 링크 기술을 쓰면 아래쪽 프레임 형식도 달라진다. ([RFC 791](https://www.rfc-editor.org/rfc/rfc791.html), [RFC 9293](https://www.rfc-editor.org/rfc/rfc9293.html))

### 4. eth 패킷의 정확한 단위는 이더넷 프레임이다

“eth 패킷”은 보통 이더넷에서 관찰하는 데이터를 뜻한다. 계층을 구분할 때는 다음 이름이 편리하다.

| 계층 또는 관점 | 부르는 단위 | 핵심 정보 |
|---|---|---|
| 애플리케이션 | 메시지·레코드 | 명령, 요청 ID, 본문 |
| TCP | 세그먼트 | 포트, 시퀀스 번호, ACK 등 |
| UDP | 데이터그램 | 포트, 길이 등 |
| IP | 패킷·데이터그램 | 출발지·목적지 IP 주소 등 |
| Ethernet | 프레임 | 출발지·목적지 MAC, EtherType 등 |

태그가 없는 **Ethernet II 프레임**은 다음처럼 볼 수 있다. 길이 계산에서는 프리앰블·SFD와 프레임 간 간격을 제외했다.

```text
[목적 MAC 6 B][출발 MAC 6 B][EtherType 2 B][데이터 46~1500 B][FCS 4 B]
```

EtherType은 담긴 프로토콜을 구분한다. 예를 들어 `0x0800`은 IPv4, `0x0806`은 ARP다. 이더넷에는 IP가 아닌 데이터도 실을 수 있으므로, 모든 이더넷 프레임을 TCP 패킷이라고 부를 수는 없다. ([RFC 894](https://www.rfc-editor.org/rfc/rfc894.html), [RFC 826](https://www.rfc-editor.org/rfc/rfc826.html))

**일반적인 Ethernet MTU 1500은 프레임 전체 크기가 아니라, 여기에 담기는 IP 패킷의 최대 크기**다. MAC 헤더 14바이트와 FCS 4바이트를 더하면 위 조건에서 최대 1518바이트다. IP 패킷이 너무 작으면 최소 데이터 필드 길이를 맞추는 패딩이 붙으며, 그 패딩은 IP 패킷에 포함되지 않는다. RFC 894의 1500바이트 설명에는 오래된 오타가 있어 [공식 정정 사항](https://www.rfc-editor.org/errata/rfc894)을 함께 확인해야 한다.

VLAN 태그, 점보 프레임, 터널을 사용하면 길이와 사용 가능한 MTU 조건이 달라진다. 또 FCS의 오류 검출이 상대 애플리케이션까지의 전달·처리 완료를 보장하는 것은 아니다.

#### 목적지 MAC은 최종 서버의 MAC일까?

일반적인 유니캐스트 라우팅에서는 **현재 링크의 다음 홉**을 가리킨다.

- 같은 서브넷으로 직접 전달하면 목적 호스트의 MAC을 사용한다.
- 다른 네트워크로 전달하면 보통 게이트웨이의 MAC을 사용한다.

예를 들어 내 PC가 외부 서버에 접속할 때, IP 목적지는 외부 서버지만 첫 번째 이더넷 프레임의 목적 MAC은 공유기일 수 있다. 라우터는 다음 링크에 맞게 프레임을 새로 구성한다. 일반적인 라우팅에서는 IP 목적지를 유지하지만, NAT나 터널이 개입하면 별도 주소 변환·캡슐화가 생긴다. IPv4의 ARP는 현재 링크에서 필요한 IP 주소와 MAC 주소의 대응을 알아내는 데 사용된다. ([RFC 1122 §3.3.1](https://www.rfc-editor.org/rfc/rfc1122.html#section-3.3.1), [RFC 826](https://www.rfc-editor.org/rfc/rfc826.html))

### 5. TCP와 UDP는 무엇을 보장할까?

| 항목 | TCP | UDP |
|---|---|---|
| 전달 모델 | 연결 지향 바이트 스트림 | 데이터그램 단위 전달 |
| 메시지 경계 | 애플리케이션이 정의 | 데이터그램 경계 유지 |
| 순서 | 수신 앱에 바이트 순서 유지 | 자체적인 순서 보장 없음 |
| 손실 대응 | 재전송 등으로 신뢰성 제공, 복구하지 못하면 실패 | 자체적인 재전송 없음 |
| 흐름·혼잡 제어 | 프로토콜에 포함 | UDP 자체에는 없음 |
| 전송 헤더 | 최소 20바이트 | 8바이트 |
| 대표적인 선택 이유 | 순서가 중요한 요청·응답과 데이터 전송 | 오래된 데이터보다 최신 데이터가 중요하거나 별도 전송 정책이 필요한 경우 |

TCP가 신뢰성을 제공한다는 것은 연결 장애와 무관하게 언제나 요청이 완료된다는 뜻이 아니다. 통신은 실패할 수 있고, 업무 처리 완료 여부는 애플리케이션에서 판단해야 한다. UDP 위에서도 별도의 프로토콜이 신뢰성이나 혼잡 제어를 구현할 수 있다. 비교 대상이 UDP 자체인지, 그 위의 프로토콜까지 포함하는지 확인하자. ([RFC 9293](https://www.rfc-editor.org/rfc/rfc9293.html), [RFC 768](https://www.rfc-editor.org/rfc/rfc768.html), [RFC 8085](https://www.rfc-editor.org/rfc/rfc8085.html))

UDP의 경계 보존도 수신 버퍼가 충분하다는 전제가 필요하다. 일반적인 수신에서는 데이터그램 하나를 읽지만, 버퍼가 작으면 초과 데이터가 잘릴 수 있다. 그 나머지가 다음 `recv()`로 이어지지 않는다. Linux에서는 `recvmsg()`의 `MSG_TRUNC` 등으로 잘림을 확인할 수 있다. ([udp(7)](https://man7.org/linux/man-pages/man7/udp.7.html), [recv(2)](https://man7.org/linux/man-pages/man2/recv.2.html))

또한 **`SOCK_DGRAM`이라고 모두 UDP인 것은 아니다.** Linux의 유닉스 도메인 데이터그램은 메시지 경계를 유지하고 신뢰성·순서 특성도 UDP와 다르다. 주소 체계와 소켓 타입을 함께 봐야 한다. ([unix(7)](https://man7.org/linux/man-pages/man7/unix.7.html))

### 6. 왜 send 한 번과 recv 한 번이 대응하지 않을까?

TCP와 유닉스 도메인의 `SOCK_STREAM`은 바이트 스트림이다. 송신자가 다음과 같이 호출했다고 하자.

```text
send("HELLO")
send("WORLD")
```

수신자는 아래와 같은 여러 형태로 읽을 수 있다.

```text
경우 A: recv() → "HELLOWORLD"
경우 B: recv() → "HEL", 다음 recv() → "LOWORLD"
경우 C: recv() → "HELLO", 다음 recv() → "WORLD"
```

바이트의 순서는 같지만 읽기 호출의 경계는 달라진다. 흔히 “패킷이 붙었다”라고 부르는 현상이지만, 애플리케이션은 TCP의 패킷 경계에 의존해서 메시지를 나누면 안 된다. `recv(n)`은 일반적으로 **최대 n바이트까지 읽는 호출**이며, 정확히 n바이트를 채우려면 반복 수신해야 한다. ([Python Socket Programming HOWTO](https://docs.python.org/3/howto/sockets.html), [recv(2)](https://man7.org/linux/man-pages/man2/recv.2.html))

메시지 경계를 정하는 대표적인 방법은 다음과 같다.

| 방법 | 형식 예시 | 설계할 부분 |
|---|---|---|
| 고정 길이 | 항상 64바이트 | 낭비 공간, 버전 변경 |
| 구분자 | 한 줄에 JSON 하나 + 줄바꿈 | 구분자 escaping, 최대 길이 |
| 길이 접두어 | 4바이트 길이 + 본문 | 길이 필드 자체의 분할 수신, 상한 검증 |

C 구조체를 그대로 보내는 것도 주의해야 한다. 구조체 패딩, 정렬, 엔디언, 정수 크기가 다를 수 있고 포인터 값은 다른 프로세스에서 같은 의미를 갖지 않는다. 각 필드의 크기와 바이트 순서를 명시하거나 JSON·Protocol Buffers 같은 직렬화 형식을 사용하자. 직렬화와 메시지 경계 처리는 별개이므로, JSON을 TCP에 실을 때도 메시지 구분 규칙이 필요하다.

## 해결 방법

### 1. 먼저 요구사항을 정하고 통신 수단을 비교한다

| 후보 | 통신 범위 | 경계 보존 | 장점 | 주요 설계 부담 |
|---|---|---|---|---|
| 파이프·FIFO | 같은 호스트 | 기본적으로 없음 | 단순한 스트림 연결 | 양방향 구성, 프레이밍 |
| POSIX 메시지 큐 | 같은 호스트 | 있음 | 메시지 단위 교환 | 큐 용량·메시지 크기 제한, 수명 관리 |
| 유닉스 도메인 스트림 | 같은 호스트 | 없음 | 양방향 요청·응답, 로컬 권한 연계 | 프레이밍, 경로·연결 관리 |
| 유닉스 도메인 데이터그램·SEQPACKET | 같은 호스트 | 있음 | 로컬 메시지 단위 교환 | 크기 제한, 플랫폼별 지원 확인 |
| TCP 소켓 | 로컬 또는 원격 | 없음 | 순서가 있는 바이트 전달, 원격 확장 | 프레이밍, 시간 제한, 재접속 |
| UDP 소켓 | 로컬 또는 원격 | 있음 | 애플리케이션이 전송 정책을 세밀하게 제어 | 손실·순서·중복·혼잡 처리 |
| 공유 메모리 | 같은 호스트 | 직접 정의 | 큰 데이터의 반복 복사를 줄일 가능성 | 동기화, 데이터 소유권, 장애 복구 |

이더넷 프레임은 위 수단들과 다른 기준에 있다. 일반적인 서비스 개발에서는 TCP·UDP 소켓을 선택하고 커널이 아래쪽 프레임 처리를 맡는다. 링크 계층 프로토콜 자체를 구현하거나 프레임을 분석할 때 `AF_PACKET` 같은 기능을 검토한다.

“공유 메모리 → 유닉스 소켓 → TCP → UDP 순서로 빠르다” 같은 고정 순위는 유용하지 않다. 작은 메시지에서는 시스템 호출과 직렬화가, 큰 버퍼에서는 복사와 메모리 대역폭이, 원격 통신에서는 지연·손실·혼잡이 크게 작용할 수 있다. 실제 메시지 크기와 동시 요청 수로 처리량, CPU 사용량, p95·p99 지연을 함께 측정해야 한다.

### 2. 메시지 규칙과 완료 조건을 따로 정한다

스트림 기반 요청·응답이라면 다음을 먼저 합의하자.

1. **프레이밍:** 메시지를 어디서 끊는가?
2. **본문 형식:** UTF-8 JSON인가, 고정된 바이너리 필드인가?
3. **제한:** 최대 길이, 읽기·쓰기 시간 제한은 얼마인가?
4. **응답:** 수신 확인인가, 업무 처리 완료인가?
5. **재시도:** 같은 요청을 다시 보내면 중복 실행되는가?

`send()`는 요청한 데이터의 일부만 보낼 수 있다. Python의 `sendall()`은 전부 보내거나 예외가 발생할 때까지 처리를 반복하지만, 성공했다고 상대 애플리케이션의 처리 완료까지 증명하지는 않는다. TCP ACK도 업무 완료 응답을 대신하지 않는다. 실패 시 일부가 이미 전달됐을 수 있으므로 재시도에는 요청 ID와 중복 처리 정책이 필요하다. ([Python socket.sendall](https://docs.python.org/3/library/socket.html#socket.socket.sendall), [send(2)](https://man7.org/linux/man-pages/man2/send.2.html))

### 3. MTU와 애플리케이션 메시지 크기를 구분한다

MTU 1500인 경로에서 옵션 없는 IPv4 헤더 20바이트를 가정하면 다음과 같이 계산할 수 있다.

```text
TCP: 1500 - IPv4 헤더 20 - TCP 기본 헤더 20 = 데이터 1460바이트
UDP: 1500 - IPv4 헤더 20 - UDP 헤더 8      = 본문 1472바이트
```

TCP의 1460바이트는 이 조건에서의 기본적인 MSS 계산 예다. 옵션과 실제 경로 조건에 따라 달라진다. 앱이 1 MiB 메시지를 보내도 TCP가 여러 세그먼트로 나누어 운반할 수 있으므로, 애플리케이션 메시지를 반드시 MSS 이하로 제한해야 하는 것은 아니다.

반면 **UDP 본문 1500바이트는 IPv4 기준으로 총 1528바이트**가 되어 MTU 1500에 맞지 않는다. 경로 MTU 탐색과 설정에 따라 전송 오류가 나거나 IP 단편화가 발생할 수 있다. 데이터그램을 크게 만드는 것이 유리하다고 단정할 수 없다. 최대 크기보다 경로 MTU와 단편화 회피가 실무에서 더 중요하다. 위 1472바이트도 IPv6·터널·더 작은 경로 MTU에 공통으로 적용되는 안전값은 아니다. ([RFC 894 정정 사항](https://www.rfc-editor.org/errata/rfc894), [RFC 9293 §3.7.1](https://www.rfc-editor.org/rfc/rfc9293.html#section-3.7.1), [RFC 8085 §3.2](https://www.rfc-editor.org/rfc/rfc8085.html#section-3.2))

## 예제

### 길이 접두어로 TCP 메시지 구분하기

다음 예제는 서버와 클라이언트를 **별도 프로세스**로 실행한다. 같은 호스트의 루프백 TCP를 사용하므로 실제 요청·응답은 오가지만 외부 물리 NIC를 거치지 않는다.

메시지 형식은 `[본문 바이트 길이: 4바이트 big-endian][UTF-8 JSON 본문]`이다. 길이는 헤더를 제외한 본문 크기이며, 최대 1 MiB로 제한한다. `socket_message_demo.py`로 저장한다.

```python
import argparse
import json
import socket
import struct


MAX_MESSAGE = 1024 * 1024


def recv_exact(sock, size):
    data = bytearray()
    while len(data) < size:
        chunk = sock.recv(size - len(data))
        if not chunk:
            raise EOFError("connection closed before message completed")
        data.extend(chunk)
    return bytes(data)


def send_message(sock, message):
    body = json.dumps(message, ensure_ascii=False).encode("utf-8")
    if not 0 < len(body) <= MAX_MESSAGE:
        raise ValueError("invalid message size")
    header = struct.pack("!I", len(body))
    sock.sendall(header + body)


def recv_message(sock):
    header = recv_exact(sock, 4)
    (size,) = struct.unpack("!I", header)
    if not 0 < size <= MAX_MESSAGE:
        raise ValueError("invalid message size")
    return json.loads(recv_exact(sock, size).decode("utf-8"))


def run_server(port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as listener:
        listener.bind(("127.0.0.1", port))
        listener.listen(1)
        listener.settimeout(60)
        print(f"listening: 127.0.0.1:{port}", flush=True)
        connection, _ = listener.accept()
        with connection:
            connection.settimeout(5)
            for _ in range(2):
                message = recv_message(connection)
                print(f"received id={message['id']}", flush=True)
                # 이 예제의 처리는 메시지 출력이다.
                send_message(connection, {
                    "id": message["id"], "status": "processed"
                })


def run_client(port):
    messages = [
        {"id": 1, "text": "안녕하세요"},
        {"id": 2, "text": "두 번째 메시지"},
    ]
    with socket.create_connection(("127.0.0.1", port), timeout=5) as sock:
        for message in messages:
            send_message(sock, message)
            reply = recv_message(sock)
            print(f"reply id={reply['id']} status={reply['status']}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("role", choices=["server", "client"])
    parser.add_argument("--port", type=int, default=5050)
    args = parser.parse_args()
    if args.role == "server":
        run_server(args.port)
    else:
        run_client(args.port)
```

첫 번째 터미널에서 서버를 실행한다.

```bash
python socket_message_demo.py server
```

두 번째 터미널에서 클라이언트를 실행한다. 서버는 연결 하나에서 메시지 두 개를 처리한 뒤 종료한다.

```bash
python socket_message_demo.py client
```

`5050` 포트가 사용 중이면 양쪽 명령에 같은 `--port 5051` 옵션을 추가한다.

예제의 핵심은 세 부분이다.

- `struct.pack("!I", ...)`로 길이를 4바이트 네트워크 바이트 순서로 표현한다.
- `recv_exact()`가 헤더와 본문을 각각 끝까지 모은다. 헤더 4바이트도 한 번에 들어온다고 가정하지 않는다.
- 상대가 보낸 길이를 검증한 뒤 본문을 읽는다. 한글은 UTF-8에서 여러 바이트이므로 문자 수가 아닌 인코딩한 바이트 수를 사용한다.

실제 서버에는 JSON 필드·타입 검증, 요청 전체의 마감 시간, 인증과 접근 제어, 동시 연결 처리도 필요하다. 이 예제의 `settimeout()`은 개별 소켓 작업의 대기 제한이며, 메시지 전체를 받는 총시간 제한을 대신하지는 않는다.

## 결과 확인

서버와 클라이언트의 출력은 다음과 같다.

```text
# 서버
listening: 127.0.0.1:5050
received id=1
received id=2

# 클라이언트
reply id=1 status=processed
reply id=2 status=processed
```

수신 데이터가 여러 조각으로 나뉘어도 길이만큼 모은 다음 JSON을 해석한다. 여러 메시지가 연달아 도착해도 한 메시지에 필요한 길이만 읽으므로 다음 메시지를 구분할 수 있다. **수신 호출 횟수나 TCP 세그먼트 개수에 관계없이 앱의 메시지 규칙으로 해석하는 것**이 목적이다.

응답의 `processed`는 이 예제에서 메시지 출력까지 끝났다는 약속이다. 실제 서비스에서 DB 반영 완료를 뜻하게 하려면 그 작업이 끝난 뒤 응답해야 한다. 요청 ID를 넣는 것만으로 중복 실행이 방지되는 것은 아니며, 서버의 중복 확인·결과 보관 정책도 있어야 한다.

같은 길이 접두어 규칙은 유닉스 도메인 `SOCK_STREAM`에도 사용할 수 있다. 주소와 연결 설정은 바뀌지만 바이트 스트림에서 메시지를 복원하는 원리는 같다.

## 실무 팁

### 흔한 실수

| 흔한 가정 | 실제로 확인할 것 |
|---|---|
| `send()` 한 번이면 메시지 하나가 도착한다 | 부분 송신과 스트림 프레이밍 |
| `recv(4096)`은 4096바이트를 채워 준다 | 반환 길이와 연결 종료 |
| 로컬 소켓은 모두 메시지 경계를 유지한다 | `SOCK_STREAM` / `SOCK_DGRAM` / `SOCK_SEQPACKET` 구분 |
| UDP에서 잘린 본문은 다음 수신으로 읽으면 된다 | 데이터그램 잘림 감지와 버퍼 크기 |
| `sendall()` 성공이면 업무가 끝났다 | 앱 응답의 의미와 재시도 정책 |
| MAC 주소는 원격 서버까지 계속 같다 | 현재 링크의 다음 홉과 라우팅 경로 |
| TCP 통신은 이더넷 인터페이스에서 항상 보인다 | 루프백·컨테이너·네트워크 네임스페이스와 캡처 위치 |

### 주의사항

**느린 수신자와 큐 적체도 통신 설계에 포함한다.** 커널 소켓 버퍼나 메시지 큐가 가득 차면 송신이 대기하거나 실패할 수 있다. 애플리케이션이 메모리 큐에 무제한으로 쌓는다면 메모리 부족으로 이어질 수 있다. 큐 상한, 대기 시간, 거절·폐기 정책으로 역압력(backpressure)을 처리하자.

**공유 메모리를 쓴다고 동기화가 사라지지는 않는다.** 누가 쓰고 읽는지, 데이터가 언제 완성되는지, 슬롯을 언제 재사용하는지, 프로세스가 죽으면 어떻게 복구할지 정해야 한다. 큰 데이터는 공유 메모리로 전달하고 제어 메시지는 로컬 소켓으로 보내는 조합도 가능하다.

**캡처 화면의 패킷이 선로의 프레임과 항상 일치하지는 않는다.** TSO·GSO는 분할을 뒤로 미루고, GRO는 수신 데이터를 합칠 수 있다. 송신 체크섬 오프로딩 때문에 캡처 시점에는 체크섬이 아직 완성되지 않았을 수도 있다. MTU보다 큰 데이터나 잘못된 체크섬 표시를 보면 캡처 지점과 오프로딩 상태를 함께 확인하자. ([Linux Segmentation Offloads](https://docs.kernel.org/networking/segmentation-offloads.html), [Linux Checksum Offloads](https://docs.kernel.org/networking/checksum-offloads.html))

### 추천 명령어

아래는 Linux에서 사용하는 명령어다. 인터페이스 이름과 포트는 실제 환경에 맞춘다.

```bash
# 유닉스 도메인 소켓, TCP, UDP 상태
ss -xap
ss -tnp
ss -unp

# 인터페이스 이름과 MTU 확인
ip -br link
ip link show dev eth0

# 예제의 루프백 TCP 관찰: 서버를 시작한 뒤 클라이언트 실행 전에 캡처
sudo tcpdump -i lo -nn 'tcp port 5050'

# 물리 인터페이스에서 MAC 헤더까지 관찰
# 원격 호스트와 이 인터페이스로 통신하는 트래픽이 있어야 한다.
sudo tcpdump -i eth0 -e -nn 'arp or tcp port 5050'

# NIC 오프로딩 상태 확인
ethtool -k eth0
```

`ss`의 프로세스 정보는 권한에 따라 일부 보이지 않을 수 있다. 유닉스 도메인 소켓의 본문은 일반적인 NIC 패킷 캡처에서 보이지 않는다. 이 경우 애플리케이션 로그와 시스템 호출 추적 등 관찰 지점을 바꿔야 한다.

## 마무리

### 핵심 요약

- **IPC:** 프로세스 사이에서 데이터와 상태를 교환하는 방법의 범주다.
- **IPC 패킷:** 보통 해당 프로그램이 정의한 메시지다. 공통 표준 형식은 없다.
- **소켓:** 로컬 통신과 네트워크 통신 등에 사용하는 운영체제 인터페이스다.
- **TCP·UDP:** 서로 다른 전달 특성을 제공하는 전송 계층 프로토콜이다.
- **IP 패킷:** 네트워크를 거쳐 목적지로 전달되는 단위다.
- **이더넷 프레임:** 현재 이더넷 링크에서 전달하는 단위다.

### 언제 사용하면 좋은가

로컬 요청·응답에는 유닉스 도메인 소켓을, 단순 스트림 연결에는 파이프를 검토할 수 있다. 큰 데이터를 반복 공유한다면 공유 메모리의 이점과 동기화 비용을 측정한다. 원격에서 순서가 있는 전달이 필요하면 TCP가 유력한 후보이며, 손실·지연 정책을 직접 설계해야 한다면 UDP와 그 위의 프로토콜을 검토한다.

### 추가 학습 주제

다음 단계로는 `epoll` 기반 동시 연결 처리, 공유 메모리 링 버퍼의 소유권과 동기화, 요청 재시도의 멱등성, 경로 MTU 탐색, 패킷 캡처 위치에 따른 오프로딩 차이를 살펴보면 좋다.

## 참고 자료

- [Linux man-pages: socket(2)](https://man7.org/linux/man-pages/man2/socket.2.html) — 소켓 주소 체계와 타입
- [Linux man-pages: unix(7)](https://man7.org/linux/man-pages/man7/unix.7.html) — 유닉스 도메인 소켓과 로컬 IPC
- [Linux man-pages: pipe(7)](https://man7.org/linux/man-pages/man7/pipe.7.html), [mq_overview(7)](https://man7.org/linux/man-pages/man7/mq_overview.7.html), [shm_overview(7)](https://man7.org/linux/man-pages/man7/shm_overview.7.html) — IPC 수단별 전달 특성
- [RFC 9293: TCP](https://www.rfc-editor.org/rfc/rfc9293.html), [RFC 768: UDP](https://www.rfc-editor.org/rfc/rfc768.html), [RFC 8085: UDP Usage Guidelines](https://www.rfc-editor.org/rfc/rfc8085.html) — 전송 특성과 메시지 크기 설계
- [RFC 791: IP](https://www.rfc-editor.org/rfc/rfc791.html), [RFC 894: IP over Ethernet](https://www.rfc-editor.org/rfc/rfc894.html), [RFC 894 정정 사항](https://www.rfc-editor.org/errata/rfc894), [RFC 826: ARP](https://www.rfc-editor.org/rfc/rfc826.html) — 패킷·프레임과 주소 관계
- [Python Socket Programming HOWTO](https://docs.python.org/3/howto/sockets.html), [Python socket API](https://docs.python.org/3/library/socket.html) — 송수신과 메시지 프레이밍
- [Linux man-pages: packet(7)](https://man7.org/linux/man-pages/man7/packet.7.html) — Linux 링크 계층 소켓
- [Linux Kernel: Segmentation Offloads](https://docs.kernel.org/networking/segmentation-offloads.html), [Checksum Offloads](https://docs.kernel.org/networking/checksum-offloads.html) — 캡처를 해석할 때 고려할 오프로딩
