---
title: "HTS 자동화가 중간에 멈출 때: 로그인 완료 대기와 팝업 처리"
description: "HTS 로그인 자동화에서 sleep만 늘려도 멈추는 이유를 살펴보고, 화면 상태 확인·팝업 우선 처리·전체 제한 시간·실패 로그를 Python 재현 예제로 구현합니다."
date: 2026-11-03 00:00:00 +0900
categories: [python, automation]
tags: [python, HTS, pyautogui, 자동화, login-automation, 팝업처리, timeout]
toc: true
image:
  path: /assets/img/2026-11-03-hts-login-wait-flow.svg
  alt: "HTS 로그인 완료 대기와 팝업 처리 흐름"
---

## 들어가며

HTS를 실행하고 인증서 비밀번호까지 입력했는데 다음 단계에서 멈춘다. 어제는 잘 동작했지만 오늘은 공지 팝업이 하나 더 떴다. 대기 시간을 늘리면 잠깐 해결되는 것 같다가 다시 비슷한 문제가 생긴다.

이럴 때는 **몇 초가 지났는지보다, 다음 단계로 넘어갈 화면 조건이 갖춰졌는지** 확인해야 한다. 프로세스가 실행 중이라는 사실, 창이 보인다는 사실, 로그인이 끝났다는 사실은 서로 다르다.

앞선 [삼성증권 HTS 자동 매매 구현기]({% post_url 2026-03-07-samsung_hts_auto_trade_post %})와 [POP HTS 실행·로그인 코드]({% post_url 2026-03-08-hts-login %})에서 시작과 로그인 흐름을 다뤘다. 이번에는 **로그인 요청 이후부터 메인 화면 준비를 확인할 때까지의 대기 정책**에 집중한다.

아래 예제는 화면 상태를 미리 정한 데모로 검증했다. 실제 HTS를 실행하거나 인증 정보를 입력하지 않는다. 화면을 읽는 부분을 분리했기 때문에 대기 로직부터 독립적으로 실행해 볼 수 있다.

## 문제 상황: sleep을 늘려도 같은 위치에서 멈춘다

인증 처리를 요청한 뒤 5초 기다리고 다음 버튼을 누르는 코드가 있다고 하자. 화면이 3초 만에 준비되면 불필요하게 기다리고, 8초가 걸리면 아직 준비되지 않은 화면을 조작하게 된다.

대기 시간을 10초로 늘리면 느린 경우 일부를 통과할 수는 있다. 그러나 예상하지 못한 팝업, 인증 실패 메시지, 포커스 변경까지 해결되는 것은 아니다.

| 관찰한 현상 | 구분해서 확인할 것 |
|---|---|
| HTS 프로세스가 있는데 진행되지 않는다 | 로그인 창인지, 처리 중인지, 메인 화면인지 |
| 메인 화면은 보이는데 다음 동작이 안 된다 | 앞을 가린 팝업과 대상 요소의 활성 상태 |
| 확인 버튼을 계속 누른다 | 이전 닫기 요청의 결과를 확인했는지 |
| 무한 대기하는 것처럼 보인다 | 상태 변경 때마다 타이머를 초기화하는지 |
| 로그에는 오류 한 줄만 남는다 | 마지막 상태·경과 시간·예외 종류가 있는지 |

이미지 파일 자체를 읽지 못하거나 배율 때문에 검색이 실패한다면 [PyAutoGUI 이미지 인식 진단]({% post_url 2026-03-01-pyautogui_image_recognition_advanced %})에서 먼저 원인을 좁히자. 이번 글은 이미지 한 장을 찾는 방법보다, **여러 화면 상태를 어떤 순서와 제한 안에서 처리할지**를 다룬다.

## 원인 분석: 화면 관찰과 처리 정책이 섞여 있다

### 화면 관찰은 현재 상황을 알려 준다

예제에서는 관찰 결과를 `Observation`으로 표현한다. 실제 연결 시에는 이미지 검색이나 UI 요소 조회가 이 값을 채운다.

| 관찰값 | 의미 | 대기 정책 |
|---|---|---|
| `login=True` | 로그인 화면이 아직 보인다 | 로그인 요청을 다시 보내지 않고 관찰 |
| `loading=True` | 식별 가능한 처리 중 화면이다 | 제한 시간 안에서 관찰 |
| `popup="login_notice"` | 사전에 확인한 공지다 | 닫기 요청 후 사라짐 확인 |
| 그 밖의 `popup` 값 | 자동 처리 대상으로 정하지 않은 대화상자다 | 중단하고 확인 |
| `ready=True` | 정의한 준비 조건이 충족됐다 | 팝업·로그인·로딩이 없을 때 연속 확인 |
| 아무 조건도 충족되지 않음 | 현재 화면을 판별하지 못했다 | 클릭하지 않고 전체 제한 시간 안에서 관찰 |

`login_notice`는 **이 예제에서 정한 식별자**다. 특정 증권사의 실제 창 제목이나 공지 내용이 아니다.

### 정책은 다음 행동을 결정한다

대기 함수는 ‘보이는 확인 버튼은 전부 누른다’는 규칙을 사용하지 않는다. **식별한 공지인지 확인하고, 한 번 닫기를 요청한 뒤 그 결과를 다시 관찰한다.**

팝업 뒤에 메인 화면이 보이는 상황도 중요하다. `ready=True`와 `popup`이 함께 관찰되면 팝업을 먼저 처리해야 한다. 준비 화면 이미지만 찾고 성공을 반환하면 가려진 화면을 완료로 오판할 수 있다.

상단 그림은 가능한 전환 경로 중 하나다. 공지가 없으면 준비 확인으로 바로 넘어갈 수 있으며, 실제 HTS 화면을 캡처한 그림은 아니다.

## 해결 방법: 대기 규칙 네 가지를 정한다

### 1. 준비 조건을 먼저 정의한다

‘HTS라는 이름의 창이 존재한다’만으로 로그인 완료를 판단하지 않는다. 실제 환경에서는 다음 조건을 조합할 수 있다.

- 로그인 화면과 로딩 표시가 사라졌다.
- 기대한 메인 창이 올바른 프로세스에 속한다.
- 다음 작업에 필요한 메뉴나 요소가 보이고 사용할 수 있다.
- 진행을 막는 대화상자가 없다.

이것은 다음 UI 단계의 준비 조건이다. 서버 연결·계좌 조회·주문 가능 상태처럼 업무상 확인이 필요한 조건은 별도로 정의해야 한다.

### 2. 전체 제한 시간을 유지한다

상태가 바뀔 때마다 시간을 다시 재면 `LOADING → POPUP → LOADING`을 반복하면서 대기가 계속 연장될 수 있다. 시작할 때 전체 마감 시간을 한 번 계산하고 끝까지 유지한다.

경과 시간에는 시스템 시각 변경의 영향을 받지 않는 [`time.monotonic()`](https://docs.python.org/3.14/library/time.html#time.monotonic)을 사용한다. 화면을 관찰하는 호출 자체가 오래 걸릴 수 있으므로 호출 전후에 시간을 확인한다. 다만 이 방식은 **실행 중인 화면 조회를 강제로 중단하는 타이머는 아니다.** 조회나 클릭 함수에도 필요하면 별도의 제한이 있어야 한다.

### 3. 같은 팝업을 연속으로 누르지 않는다

닫기 요청 이후에도 팝업이 보이면, 닫기 동작을 반복하지 않고 사라지는지 기다린다. 별도의 짧은 제한 안에 사라지지 않으면 `PopupNotClosed`로 중단한다.

한 번 사라진 공지가 다시 나타나는 경우에는 새 닫기 요청이 가능하지만, 예제에서는 전체 요청 수를 두 번으로 제한했다. 이 횟수와 시간 값은 **재현용 설정**이며 실제 HTS의 권장 수치가 아니다.

### 4. 준비 화면을 연속 관찰한다

예제는 준비 상태를 두 번 연속 관찰한 뒤 반환한다. 중간에 로그인·로딩·팝업·미확인 상태가 나오면 확인 횟수를 초기화한다.

연속 관찰은 잠깐 보인 화면으로 다음 단계에 넘어가는 것을 줄이기 위한 규칙이다. 두 번 확인했다고 실제 인증이나 서버 처리가 보장되는 것은 아니며, 관찰 조건 자체가 정확해야 한다.

## 예제: 실제 화면 없이 대기 정책을 실행한다

### 전체 코드 내려받기

<a href="/assets/downloads/2026-11-03-hts-login-wait-demo.py" download="login_wait_demo.py">실행 가능한 Python 예제 다운로드</a>

파일을 **`login_wait_demo.py`**로 저장한다. Python 3.10 이상에서 동작하도록 작성했으며, 아래 실행 결과는 Python 3.14.5에서 확인했다. 데모는 표준 라이브러리만 사용하므로 추가 패키지나 HTS 설치가 필요 없다.

```powershell
python --version
python .\login_wait_demo.py --scenario notice
```

데모는 미리 정한 화면 관찰값과 **가상 시간**을 사용한다. 로그의 4초는 시뮬레이션상의 경과 시간이며, 실제 실행에 4초를 기다리거나 HTS 속도를 측정한 결과가 아니다. 팝업 닫기도 호출 기록만 남긴다.

### 화면 관찰과 대기 함수를 연결하는 핵심 코드

다음은 다운로드 파일에 포함된 핵심 부분이다. `observe()`가 현재 관찰값을 반환하고 `dismiss_notice()`가 확인한 공지에 대한 닫기 요청을 담당한다. 다운로드 파일에는 이 두 기능을 재현하는 데모와 실행 옵션까지 들어 있다.

```python
from dataclasses import dataclass
import logging
import math
import time

LOG = logging.getLogger("login_wait")


@dataclass(frozen=True)
class Observation:
    login: bool = False
    loading: bool = False
    ready: bool = False
    popup: str | None = None


class UnhandledPopup(RuntimeError):
    pass


class PopupNotClosed(RuntimeError):
    pass


class PopupLimitExceeded(RuntimeError):
    pass


def wait_for_login(observe, dismiss_notice, *, timeout=12.0,
                   interval=1.0, popup_timeout=2.0, max_popup_actions=2,
                   ready_samples=2, clock=time.monotonic, pause=time.sleep):
    for value in (timeout, interval, popup_timeout):
        if not math.isfinite(value) or value <= 0:
            raise ValueError("time limits and interval must be finite and positive")
    if type(max_popup_actions) is not int or max_popup_actions < 0:
        raise ValueError("max_popup_actions must be a nonnegative integer")
    if type(ready_samples) is not int or ready_samples < 2:
        raise ValueError("ready_samples must be an integer >= 2")

    started = clock()
    deadline = started + timeout
    pending_popup = None
    popup_requested_at = 0.0
    actions = 0
    ready_count = 0
    last_state = "START"
    polls = 0

    while True:
        if clock() >= deadline:
            raise TimeoutError(f"state={last_state} elapsed={clock() - started:.1f}s")
        view = observe()
        polls += 1
        now = clock()
        if now >= deadline:
            raise TimeoutError(f"observation exceeded deadline elapsed={now - started:.1f}s")
        if not isinstance(view, Observation):
            raise TypeError("observe() must return Observation")

        if view.popup is not None:
            state = "POPUP:" + view.popup
        elif view.login:
            state = "LOGIN"
        elif view.loading:
            state = "LOADING"
        elif view.ready:
            state = "READY"
        else:
            state = "UNKNOWN"
        if state != last_state:
            LOG.info("state=%s elapsed=%.1fs", state, now - started)
            last_state = state

        if view.popup is not None:
            ready_count = 0
            if view.popup != "login_notice":
                raise UnhandledPopup(f"popup={view.popup}")
            if pending_popup is None:
                if actions >= max_popup_actions:
                    raise PopupLimitExceeded(f"actions={actions}")
                actions += 1
                LOG.info("action=dismiss_notice attempt=%d", actions)
                dismiss_notice(view.popup)
                pending_popup = view.popup
                popup_requested_at = clock()
            elif clock() - popup_requested_at >= popup_timeout:
                raise PopupNotClosed(f"popup={pending_popup}")
        else:
            if pending_popup is not None:
                LOG.info("popup_gone=%s", pending_popup)
                pending_popup = None
            ready_count = ready_count + 1 if state == "READY" else 0
            if ready_count >= ready_samples:
                LOG.info("result=READY elapsed=%.1fs polls=%d actions=%d",
                         clock() - started, polls, actions)
                return view

        remaining = deadline - clock()
        if remaining <= 0:
            raise TimeoutError(f"state={last_state} elapsed={clock() - started:.1f}s")
        pause(min(interval, remaining))
```

함수 안의 `pause()`는 관찰 사이의 간격을 둔다. 조건 기반 대기에서도 짧은 휴식은 필요하다. 차이는 긴 시간을 무조건 기다린 뒤 진행하는 대신, **간격마다 완료 조건을 확인한다는 점**이다.

## 결과 확인

### 공지가 정상적으로 사라지는 경우

`notice` 시나리오를 실행해 얻은 로그다.

```text
INFO scenario=notice mode=virtual
INFO state=LOGIN elapsed=0.0s
INFO state=LOADING elapsed=1.0s
INFO state=POPUP:login_notice elapsed=2.0s
INFO action=dismiss_notice attempt=1
INFO state=READY elapsed=3.0s
INFO popup_gone=login_notice
INFO result=READY elapsed=4.0s polls=5 actions=1
```

2초에 공지가 나타나 닫기 요청을 한 번 기록했다. 3초에 공지가 사라지고 준비 화면이 보였지만 즉시 성공 처리하지 않았다. 4초에 준비 상태를 다시 관찰한 뒤 반환했다.

### 느린 전환과 일시적인 준비 화면

```powershell
python .\login_wait_demo.py --scenario normal
python .\login_wait_demo.py --scenario slow
python .\login_wait_demo.py --scenario brief-ready
```

검증한 결과는 다음과 같다. 모든 시간은 가상 시간이다.

| 시나리오 | 재현하는 상황 | 결과 |
|---|---|---|
| `normal` | 공지 없이 준비 화면으로 전환 | 3초에 반환, 닫기 요청 0회 |
| `slow` | 로딩이 8초 시점까지 이어짐 | 9초에 반환, 닫기 요청 0회 |
| `notice` | 준비 화면 앞에 확인한 공지 표시 | 4초에 반환, 닫기 요청 1회 |
| `brief-ready` | 준비 화면이 보였다가 로딩으로 바뀜 | 횟수를 초기화하고 4초에 반환 |
| `stuck-popup` | 닫기 요청 후에도 같은 공지가 남음 | 4초에 `PopupNotClosed` |
| `repeated-popup` | 사라진 공지가 반복해서 나타남 | 두 번 요청 후 5초에 `PopupLimitExceeded` |
| `unknown-popup` | 처리 대상으로 정하지 않은 팝업 | 2초에 `UnhandledPopup`, 닫기 요청 0회 |
| `ready-with-popup` | 준비 화면과 미확인 팝업이 동시에 관찰됨 | 즉시 `UnhandledPopup`, 준비 완료로 반환하지 않음 |
| `timeout` | 로딩 상태가 계속됨 | 12초에 `TimeoutError` |
| `deadline-with-popup` | 제한 시간 직전에 공지가 나타남 | 시간을 초기화하지 않고 12초에 `TimeoutError` |

### 실패 로그와 종료 코드를 함께 확인한다

```powershell
python .\login_wait_demo.py --scenario stuck-popup --output-dir .\diagnostics\stuck
$LASTEXITCODE
Get-Content .\diagnostics\stuck\failure.json
```

실패 시 종료 코드는 `1`이다. 다음은 실행 로그에서 traceback을 제외한 부분이다. 전체 traceback은 `login-wait.log`에 함께 기록된다.

```text
INFO scenario=stuck-popup mode=virtual
INFO state=LOGIN elapsed=0.0s
INFO state=LOADING elapsed=1.0s
INFO state=POPUP:login_notice elapsed=2.0s
INFO action=dismiss_notice attempt=1
ERROR result=STOP reason=PopupNotClosed elapsed=4.0s
```

`failure.json`에는 시나리오, 예외 종류, 경과 시간, 마지막 관찰값, 닫기 요청 기록이 남는다. 이 데모에는 실제 화면이 없으므로 스크린샷은 생성하지 않는다.

실제 자동화에서는 상태 관찰과 대상 영역의 캡처를 함께 남기면 당시 화면을 비교하기 쉽다. 계좌·인증 정보가 불필요하게 포함되지 않도록 저장 영역과 공유할 이미지를 확인하자. 예외를 기록할 때는 [`logging.exception()`](https://docs.python.org/3.14/library/logging.html#logging.Logger.exception)으로 traceback을 남기고, 실패를 정상 종료로 바꾸지 않는다.

## 실제 HTS 화면에 연결할 때

### observe: 한 번 관찰한 화면을 일관되게 분류한다

실제 관찰기는 이미지 검색이나 UI 요소 조회로 `Observation`을 만들어야 한다. 캡처 시점이 다른 이미지 결과를 섞으면 이미 사라진 로그인 창과 새로 뜬 메인 화면이 동시에 존재하는 것처럼 판단할 수 있다. 이미지 방식을 쓴다면 한 번 캡처한 대상 영역에서 관련 템플릿을 비교하는 방법을 검토한다.

[PyAutoGUI 공식 문서](https://pyautogui.readthedocs.io/en/latest/screenshot.html)는 `screenshot()`으로 얻은 이미지와 `locate(needleImage, haystackImage)`를 사용할 수 있도록 설명한다. 미검출 예외와 파일 읽기 오류는 구분하고, 검색 영역·배율·템플릿은 자신의 화면에서 확인해야 한다.

| 관찰 대상 | 실제 연결 시 확인할 내용 |
|---|---|
| 메인 창 | 대상 PID나 창 핸들, 가려짐과 활성 상태 |
| 준비 요소 | 다음 작업에 필요한 요소의 존재·표시·사용 가능 상태 |
| 공지 | 제목뿐 아니라 확인한 내용과 버튼이 해당 창에 속하는지 |
| 다른 대화상자 | 인증 오류·추가 확인 요청 등 처리 규칙에 없는 창 |

UI 요소가 노출되는 앱에서는 pywinauto의 `wait()`·`wait_not()`으로 요소가 나타나거나 사라지는 조건을 기다릴 수도 있다. 다만 특정 요소가 보인다는 사실과 앱의 모든 초기화가 끝났다는 사실은 다를 수 있으므로 실제 완료 조건을 따로 정한다. [pywinauto 대기 문서](https://pywinauto.readthedocs.io/en/latest/wait_long_operations.html)

**이 대기 함수가 알 수 없는 팝업을 자동으로 찾아 주는 것은 아니다.** 관찰기가 막는 대화상자를 발견했다면 해당 `popup` 값을 반환해야 한다. 화면 상태를 확신하지 못하면 `Observation()`처럼 미확인 상태로 두고, 준비 조건이 충족됐다고 추정하지 않는다.

### dismiss_notice: 확인한 공지에 한 번만 요청한다

실제 닫기 함수는 대상 앱과 공지 내용을 다시 확인한 뒤, 그 공지에 속한 버튼을 찾아 한 번 조작하도록 작성한다. 앞선 관찰 이후 다른 창이 활성화됐거나 버튼을 확신할 수 없다면 예외로 중단한다.

‘확인’이라는 글자만 보고 누르거나 `Esc`를 반복해서 보내는 방식은 사용하지 않는다. 인증 실패·추가 인증·약관 확인 같은 화면은 단순 공지와 처리 의미가 다르다. 한 번 요청한 뒤 실제로 사라졌는지는 대기 함수의 다음 관찰에서 확인한다.

실제 클릭 어댑터는 HTS 버전과 화면 구성에 맞춰 검증해야 한다. 이 글에서 실행 확인한 범위는 **데모 관찰값에 대한 대기·중단·로그 정책**이며, 특정 증권사 화면 인식이나 로그인 성공을 검증한 코드는 아니다.

## 실무 팁

### 흔한 실수

- **로그인 요청까지 재시도한다:** 화면 대기 실패를 인증 요청 재전송과 연결하지 않는다. 먼저 현재 상태를 확인한다.
- **타이머를 다시 시작한다:** 상태 전환이나 팝업 출현이 전체 제한 시간을 연장하지 않도록 한다.
- **반환값만 보고 진행한다:** 준비 화면의 판별 조건이 실제 다음 작업에 충분한지 확인한다.
- **모든 예외를 계속 무시한다:** 파일 오류, 대상 창 상실, 사용자 중단은 미검출 대기와 구분한다.

### 주의사항

PyAutoGUI를 연결할 때는 페일세이프를 유지하고 `FailSafeException`을 계속 재시도하는 예외 처리로 감싸지 않는다. [공식 페일세이프 설명](https://pyautogui.readthedocs.io/en/latest/index.html#fail-safes)

직접 실행에서는 되는데 작업 스케줄러에서만 실패한다면 대기 시간부터 늘리지 말고 [실행 계정·로그온 조건·시작 위치]({% post_url 2026-03-06-task_scheduler %})를 확인한다. 화면을 관찰할 수 없는 세션에서는 대기 정책만 바꿔도 해결되지 않는다.

### 추천 명령어

전체 제한 시간이 유지되는지 확인하려면 다음 시나리오를 실행한다.

```powershell
python .\login_wait_demo.py --scenario deadline-with-popup --output-dir .\diagnostics\deadline
Get-Content .\diagnostics\deadline\login-wait.log
```

로그인이 완료되지 않았으므로 이 명령은 종료 코드 `1`로 끝나는 것이 기대 결과다. 실패 재현과 성공 재현을 구분해서 확인하자.

## 마무리

### 핵심 요약

프로세스 실행 여부와 로그인 준비 상태를 구분한다. 팝업을 먼저 확인하고, 확인한 공지에만 닫기를 요청하며, 사라짐과 준비 상태를 다시 관찰한다. 전체 제한 시간은 상태 전환과 관계없이 유지한다.

### 언제 사용하면 좋은가

실행마다 준비 시간이 달라지거나 로그인 뒤 공지가 간헐적으로 나타나는 GUI 자동화에 적용할 수 있다. 관찰 규칙을 실제 앱에 맞춰 검증한 뒤 대기 정책과 연결한다.

### 추가 학습 주제

화면을 일정하게 맞추는 작업은 [PyGetWindow로 대상 창 제어하기]({% post_url 2026-03-01-pyautogui_pygetwindow_guide %})에서, 이미지 미검출 처리는 [PyAutoGUI 검색 영역과 예외 처리]({% post_url 2026-03-01-pyautogui_image_recognition_advanced %})에서 이어서 볼 수 있다.

## 참고 자료

- [Python 3.14: time.monotonic](https://docs.python.org/3.14/library/time.html#time.monotonic)
- [Python 3.14: Logger.exception](https://docs.python.org/3.14/library/logging.html#logging.Logger.exception)
- [PyAutoGUI: Screenshot Functions](https://pyautogui.readthedocs.io/en/latest/screenshot.html)
- [PyAutoGUI: Fail-Safes](https://pyautogui.readthedocs.io/en/latest/index.html#fail-safes)
- [pywinauto: Waiting for Long Operations](https://pywinauto.readthedocs.io/en/latest/wait_long_operations.html)
