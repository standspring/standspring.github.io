---
title: "Python os.environ에서 no_proxy와 NO_PROXY는 차이가 있을까?"
date: 2026-06-01
categories: [python, network]
tags: [python, proxy, no_proxy, NO_PROXY, os.environ, urllib, requests, httpx, curl, 환경변수]
---

![Python no_proxy와 NO_PROXY 비교](/assets/img/2026-06-01-python-no-proxy-case.svg)

# Python `os.environ`에서 `no_proxy`와 `NO_PROXY`는 차이가 있을까?

프록시를 쓰는 환경에서는 보통 아래처럼 설정한다.

```python
import os

os.environ["HTTP_PROXY"] = "http://proxy.example.com:8080"
os.environ["HTTPS_PROXY"] = "http://proxy.example.com:8080"
os.environ["NO_PROXY"] = "localhost,127.0.0.1,.example.com"
```

그런데 어떤 예제는 `NO_PROXY`를 쓰고, 어떤 예제는 `no_proxy`를 쓴다.

```python
os.environ["no_proxy"] = "localhost,127.0.0.1"
os.environ["NO_PROXY"] = "localhost,127.0.0.1"
```

둘은 같은 것일까? 결론부터 말하면 **의미는 거의 같지만, 모든 프로그램이 완전히 같은 방식으로 처리하지는 않는다.**

---

## 1. `os.environ` 자체는 그냥 환경변수 딕셔너리다

Python의 `os.environ`은 운영체제 환경변수를 Python에서 다루기 위한 매핑이다. 중요한 점은 `os.environ`이 프록시 규칙을 직접 해석하지 않는다는 것이다.

```python
import os

os.environ["no_proxy"] = "localhost"
os.environ["NO_PROXY"] = "127.0.0.1"
```

이 값을 실제로 어떻게 사용할지는 `urllib`, `requests`, `httpx`, `curl`, `wget`, Go 런타임 같은 **네트워크 클라이언트 구현체**가 결정한다.

또 하나의 함정이 있다. **Windows 환경변수 이름은 일반적으로 대소문자를 구분하지 않는다.** 그래서 Windows의 Python에서는 `os.environ["no_proxy"]`와 `os.environ["NO_PROXY"]`를 서로 다른 두 변수처럼 안정적으로 유지하기 어렵다. 마지막에 설정한 값이 같은 키의 값처럼 동작할 수 있다.

반대로 Linux/macOS 같은 POSIX 계열에서는 환경변수 이름이 대소문자를 구분하므로 `no_proxy`와 `NO_PROXY`가 동시에 존재할 수 있다.

---

## 2. Python 표준 라이브러리 `urllib.request`

Python 표준 라이브러리의 `urllib.request.getproxies()`는 환경변수에서 프록시 설정을 읽는다.

공식 문서 기준 동작은 다음과 같다.

| 항목 | 동작 |
| --- | --- |
| `http_proxy`, `HTTP_PROXY`, `https_proxy`, `HTTPS_PROXY`, `no_proxy`, `NO_PROXY` | 대소문자를 구분하지 않는 방식으로 탐색 |
| 소문자와 대문자가 둘 다 있고 값이 다름 | **소문자 우선** |
| 환경변수에서 프록시를 못 찾음 | macOS/Windows에서는 시스템 프록시 설정도 확인 |
| `REQUEST_METHOD`가 있음 | CGI 환경으로 보고 `HTTP_PROXY`를 무시 |

즉 Python 표준 라이브러리만 놓고 보면, POSIX 계열에서는 다음처럼 이해하면 된다.

```bash
export no_proxy="localhost,127.0.0.1"
export NO_PROXY="example.com"
```

두 값이 충돌하면 Python 문서상 `no_proxy`가 우선이다. 다만 Windows에서는 환경변수 자체가 대소문자 비구분으로 다뤄지므로 이 상황을 그대로 재현하기 어렵다.

### `HTTP_PROXY`만 특별히 조심해야 한다

`NO_PROXY`보다 더 위험한 쪽은 사실 `HTTP_PROXY`다.

CGI 환경에서는 HTTP 요청 헤더가 `HTTP_` 접두사의 환경변수로 바뀔 수 있다. 예를 들어 외부 요청에 `Proxy: evil` 같은 헤더가 들어오면 CGI 프로그램에서 `HTTP_PROXY` 환경변수처럼 보일 수 있다.

그래서 Python은 `REQUEST_METHOD` 환경변수가 있으면 `HTTP_PROXY`를 무시한다. curl도 같은 이유로 HTTP 프록시 변수는 `http_proxy` 소문자만 받는 정책을 갖고 있다.

---

## 3. `requests`는 무엇을 보나?

`requests`는 기본적으로 환경변수 프록시 설정을 사용한다.

공식 문서에는 `http_proxy`, `https_proxy`, `no_proxy`, `all_proxy`를 사용하며, 대문자 변형도 지원한다고 되어 있다.

```bash
export HTTP_PROXY="http://proxy.example.com:8080"
export HTTPS_PROXY="http://proxy.example.com:8080"
export NO_PROXY="localhost,127.0.0.1,.example.com"
```

그리고 Python 코드에서는 그냥 호출해도 환경변수를 참조한다.

```python
import requests

requests.get("https://www.example.com")
```

주의할 점은 `requests.Session().proxies`에 값을 넣어도 환경변수 프록시가 다시 섞일 수 있다는 점이다. 문서에서도 환경 프록시가 세션 프록시 값을 덮어쓸 수 있으니, 확실히 고정하려면 개별 요청에 `proxies=`를 명시하라고 안내한다.

환경변수를 아예 무시하고 싶으면 다음처럼 `trust_env`를 끈다.

```python
import requests

session = requests.Session()
session.trust_env = False

session.get("https://www.example.com")
```

---

## 4. `httpx`는 무엇을 보나?

`httpx`도 기본적으로 환경변수를 참조한다. 문서에서는 다음 변수를 중심으로 설명한다.

| 변수 | 의미 |
| --- | --- |
| `HTTP_PROXY` | HTTP 요청에 사용할 프록시 |
| `HTTPS_PROXY` | HTTPS 요청에 사용할 프록시 |
| `ALL_PROXY` | 전체 요청에 사용할 기본 프록시 |
| `NO_PROXY` | 프록시를 우회할 호스트 또는 URL 목록 |

환경변수를 무시하려면 `trust_env=False`를 사용한다.

```python
import httpx

httpx.get("https://www.example.com", trust_env=False)
```

클라이언트 단위로도 끌 수 있다.

```python
import httpx

with httpx.Client(trust_env=False) as client:
    client.get("https://www.example.com")
```

---

## 5. curl은 왜 `http_proxy`만 소문자를 고집할까?

curl은 프록시 환경변수 관례에 큰 영향을 준 도구다. curl 문서 기준으로 `https_proxy`, `ftp_proxy` 등은 대문자도 가능하지만, HTTP 프록시 변수 `http_proxy`는 소문자만 허용한다.

이유는 Python의 CGI 예외와 같다. `HTTP_PROXY`는 CGI 환경에서 외부 요청 헤더로 주입될 수 있기 때문이다.

반면 프록시 우회 목록은 curl 문서에서 `NO_PROXY`로 설명하며, `*`를 넣으면 전체 호스트가 프록시를 우회한다.

```bash
export http_proxy="http://proxy.example.com:8080"
export NO_PROXY="localhost,127.0.0.1,.example.com"
```

---

## 6. Go `net/http`는 무엇을 보나?

Go 표준 라이브러리의 `net/http.ProxyFromEnvironment`는 `HTTP_PROXY`, `HTTPS_PROXY`, `NO_PROXY`와 그 소문자 버전을 본다고 문서화되어 있다.

즉 Go로 만들어진 CLI 도구나 서버 프로그램은 다음 둘을 모두 인식할 가능성이 높다.

```bash
export NO_PROXY="localhost,127.0.0.1"
export no_proxy="localhost,127.0.0.1"
```

다만 Go 계열 구현은 Python과 우선순위가 다를 수 있다. 예를 들어 어떤 Go 기반 도구 문서는 대문자와 소문자가 둘 다 있을 때 대문자를 우선한다고 설명한다. 그래서 여러 언어로 된 도구가 한 프로세스나 컨테이너 안에서 섞이면, 충돌하는 값을 두지 않는 것이 가장 좋다.

---

## 7. 비교표

| 도구/라이브러리 | `no_proxy` | `NO_PROXY` | 둘 다 있을 때 | 비고 |
| --- | --- | --- | --- | --- |
| Python `urllib.request` | 지원 | 지원 | 문서상 소문자 우선 | Windows에서는 환경변수 대소문자 구분이 약함 |
| Python `requests` | 지원 | 지원 | 내부적으로 환경 프록시 병합 | `trust_env=False`로 비활성화 가능 |
| Python `httpx` | 구현체 버전에 따라 관례 지원 가능 | 문서상 명시 | 명시적 우선순위는 문서에서 강조하지 않음 | `trust_env=False`로 비활성화 가능 |
| curl | 지원 관례가 있음 | 문서에서 `NO_PROXY` 설명 | 충돌 값은 피하는 것이 안전 | `HTTP_PROXY`는 보안상 미지원 |
| Go `net/http` | 지원 | 지원 | 구현/문서에 따라 대문자 우선인 경우 있음 | Go 기반 도구에서 자주 만남 |

핵심은 **`no_proxy`와 `NO_PROXY`의 의미는 같지만, 충돌했을 때 어느 쪽을 우선하는지는 표준으로 완전히 고정되어 있지 않다**는 점이다.

---

## 8. `NO_PROXY` 값의 형식

대부분의 도구는 쉼표로 구분된 목록을 기대한다.

```bash
NO_PROXY="localhost,127.0.0.1,.example.com,10.0.0.0/8"
```

자주 쓰는 패턴은 다음과 같다.

| 값 | 의미 |
| --- | --- |
| `localhost` | 로컬 호스트 이름 우회 |
| `127.0.0.1` | IPv4 루프백 우회 |
| `::1` | IPv6 루프백 우회 |
| `.example.com` | `www.example.com`, `api.example.com` 같은 하위 도메인 우회 |
| `example.com` | 구현체에 따라 정확히 그 호스트 또는 suffix로 해석될 수 있어 주의 |
| `*` | 모든 요청에서 프록시 우회 |
| `10.0.0.0/8` | CIDR 대역 우회. 단, 모든 도구가 CIDR을 지원하지는 않음 |

특히 CIDR은 도구마다 지원 여부가 다르다. curl은 7.86.0부터 `NO_PROXY`에 CIDR 표기를 지원한다. Python `urllib`의 문서 예시는 호스트 suffix와 `:port` 중심으로 설명한다.

---

## 9. Python에서 안전하게 설정하는 방법

Python 프로그램 내부에서 프록시 우회를 확실히 설정하려면, 여러 도구와의 호환성을 위해 대소문자를 둘 다 같은 값으로 맞추는 편이 실무적으로 안전하다.

```python
import os

no_proxy = "localhost,127.0.0.1,::1,.example.com"

os.environ["no_proxy"] = no_proxy
os.environ["NO_PROXY"] = no_proxy
```

프록시 변수도 가능하면 같은 값으로 맞춘다.

```python
import os

proxy = "http://proxy.example.com:8080"
no_proxy = "localhost,127.0.0.1,::1,.example.com"

for key in ("http_proxy", "HTTP_PROXY"):
    os.environ[key] = proxy

for key in ("https_proxy", "HTTPS_PROXY"):
    os.environ[key] = proxy

for key in ("no_proxy", "NO_PROXY"):
    os.environ[key] = no_proxy
```

단, CGI나 서버 요청을 직접 처리하는 프로그램이라면 `HTTP_PROXY`는 조심해야 한다. 외부 입력이 환경변수로 흘러들 수 있는 구조라면 소문자 `http_proxy`를 선호하고, 명시적인 프록시 설정 객체를 쓰는 편이 낫다.

---

## 10. 간단한 확인 코드

현재 Python이 프록시 환경변수를 어떻게 읽는지 보려면 다음을 실행해볼 수 있다.

```python
import os
import urllib.request

os.environ["http_proxy"] = "http://proxy.example.com:8080"
os.environ["no_proxy"] = "localhost,127.0.0.1"

print(urllib.request.getproxies())
```

출력 예시는 보통 다음과 비슷하다.

```python
{
    "http": "http://proxy.example.com:8080",
    "no": "localhost,127.0.0.1",
}
```

Windows에서는 `no_proxy`와 `NO_PROXY`를 따로 넣어 비교하는 테스트가 기대와 다르게 보일 수 있다. 그것은 Python 문제가 아니라 Windows 환경변수 모델의 영향이다.

---

## 결론

Python에서 `os.environ["no_proxy"]`와 `os.environ["NO_PROXY"]`는 **프록시 우회 목록**이라는 같은 목적을 가진다.

하지만 실제 차이는 다음 지점에서 생긴다.

1. 운영체제가 환경변수 이름의 대소문자를 구분하는가?
2. 사용하는 HTTP 클라이언트가 어느 이름을 읽는가?
3. 둘 다 있을 때 어느 값을 우선하는가?
4. CGI 보안 규칙 때문에 `HTTP_PROXY` 같은 변수가 무시되는가?

실무 권장안은 단순하다.

```python
value = "localhost,127.0.0.1,::1,.example.com"
os.environ["no_proxy"] = value
os.environ["NO_PROXY"] = value
```

**두 이름을 같은 값으로 맞추고, 서로 다른 값을 넣지 않는 것**이 가장 덜 피곤한 선택이다.

---

## 참고 문서

- [Python `urllib.request` 공식 문서](https://docs.python.org/3/library/urllib.request.html)
- [Requests Advanced Usage - Proxies](https://requests.readthedocs.io/en/latest/user/advanced/#proxies)
- [HTTPX Environment Variables](https://www.python-httpx.org/environment_variables/)
- [everything curl - Proxy environment variables](https://everything.curl.dev/usingcurl/proxies/env.html)
- [Go `net/http.ProxyFromEnvironment` 문서](https://pkg.go.dev/net/http#ProxyFromEnvironment)
